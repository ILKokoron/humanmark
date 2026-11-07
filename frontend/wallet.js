// Multi-wallet support via NEAR Wallet Selector (loaded as ES modules
// from CDN, no bundler). The visitor picks their own wallet: MyNearWallet,
// HERE, Sender, Meteor, Nightly, HOT Wallet, and more the selector offers. This page
// never holds a key; signing happens inside the chosen wallet.
// Mirrors the Binding Vow frontend wallet.js, only the contract and the
// exposed global (window.hmWallet) differ.
import { setupWalletSelector } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/core@8.10.2/+esm';
import { setupModal } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/modal-ui@8.10.2/+esm';
import { setupMyNearWallet } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/my-near-wallet@8.10.2/+esm';
import { setupHereWallet } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/here-wallet@8.10.2/+esm';
import { setupSender } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/sender@8.10.2/+esm';
import { setupMeteorWallet } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/meteor-wallet@8.10.2/+esm';
import { setupNightly } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/nightly@8.10.2/+esm';
import { setupHotWallet } from 'https://cdn.jsdelivr.net/npm/@near-wallet-selector/hot-wallet@8.10.2/+esm';

const CONTRACT = 'humanmark.bindingvow1106.testnet';
let selector = null;
let selectorPromise = null;
let modal = null;
let accountId = null;

function paint() {
  const state = document.getElementById('walletState');
  const btn = document.getElementById('btnWallet');
  if (!state || !btn) return;
  if (accountId) {
    state.textContent = 'Connected: ' + accountId;
    btn.textContent = 'Disconnect';
  } else {
    state.textContent = 'Not connected';
    btn.textContent = 'Connect wallet';
  }
}

async function ensureSelector() {
  if (selector) return selector;
  if (selectorPromise) return selectorPromise;
  selectorPromise = initSelector();
  return selectorPromise;
}

async function initSelector() {
  selector = await setupWalletSelector({
    network: 'testnet',
    contractId: CONTRACT,
    modules: [
      setupMyNearWallet(),
      setupHereWallet(),
      setupSender(),
      setupMeteorWallet(),
      setupNightly(),
      setupHotWallet(),
    ],
  });
  modal = setupModal(selector, { contractId: CONTRACT });
  const accounts = selector.store.getState().accounts;
  accountId = accounts && accounts[0] ? accounts[0].accountId : null;
  paint();
  selector.store.observable.subscribe((state) => {
    const a = state.accounts;
    accountId = a && a[0] ? a[0].accountId : null;
    paint();
  });
  return selector;
}

window.hmWallet = {
  async open() {
    const state = document.getElementById('walletState');
    const btn = document.getElementById('btnWallet');
    if (!selector) {
      if (state) state.textContent = 'Opening wallet selector...';
      if (btn) btn.disabled = true;
      try { await ensureSelector(); }
      finally { if (btn) btn.disabled = false; paint(); }
    }
    if (accountId) {
      const wallet = await selector.wallet();
      await wallet.signOut();
      accountId = null;
      paint();
    } else {
      modal.show();
    }
  },
  getAccountId() {
    return accountId;
  },
  async call(method, args, depositYocto) {
    await ensureSelector();
    if (!accountId) throw new Error('Connect your wallet first.');
    const wallet = await selector.wallet();
    const result = await wallet.signAndSendTransaction({
      receiverId: CONTRACT,
      actions: [
        {
          type: 'FunctionCall',
          params: {
            methodName: method,
            args,
            gas: '100000000000000',
            deposit: depositYocto || '0',
          },
        },
      ],
    });
    return result;
  },
};

ensureSelector().catch((e) => {
  const state = document.getElementById('walletState');
  if (state) state.textContent = 'Wallet selector failed to load: ' + e.message;
});
