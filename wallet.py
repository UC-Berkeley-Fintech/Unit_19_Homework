# Import dependencies
import subprocess
import os
import json
from dotenv import load_dotenv

from constants import *
from bit import Key, PrivateKey, PrivateKeyTestnet
from bit.network import NetworkAPI
from bit import *
from web3 import Web3
from eth_account import Account 

# Load and set environment variables
load_dotenv()
mnemonic=os.getenv("mnemonic")

# create connection for Web3 communication
connection = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

# initialize web3 middleware
connection.middleware_onion.inject(geth_poa_middleware, layer=0)

# set the mnemonic as an environment variable
mnemonic = os.getenv('MNEMONIC')

# make sure the phrase is not empty
if mnemonic == 'na':
    print("Please check your .env file for your mnemonic phrase.  No mnemonic phrase found.")
    quit()
 
# Create a function called `derive_wallets`
def derive_wallets(mnemonic_phrase, coin, num_to_derive):
    """Derives wallet keys based on a single mnemonic string
    Args:
        mnemonic_phrase (str): Mnemonic string of phrases to use
        coin (str): Coin to generate keys in (example: BTC, BTCTEST, ETH, etc.)
        num_to_derive (int): Number of child keys to derive
    Returns:
        JSON object with path, address, private keys and public keys
    """
    command = command = f'php derive -g --mnemonic="{mnemonic_phrase}" --coin={coin} --numderive={num_to_derive} --cols=address,index,path,privkey,pubkey,pubkeyhash,xprv,xpub --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
coins = {
    ETH: derive_wallets(mnemonic, ETH, 3),
    BTCTEST: derive_wallets(mnemonic, BTCTEST, 3),
    BTC: derive_wallets(mnemonic, BTC, 3)
}

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    """Will convert the private key string in a child key to an account object
    Args:
        coin (str): The coin type defined in constants.py
        priv_key (str): The private key of the coin
    Returns:
        An account private key.  If converting BTCTEST, will return a Wallet
        Import Format (WIF) object.
    """
    # check the coin for ETH
    if coin == ETH:
        return Account().privateKeyToAccount(priv_key)
    # check the coin for BTCTEST
    if coin == BTCTEST:
         account = PrivateKeyTestnet(priv_key)
         print(account)
         print(account.address)
         return account

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):
    """This will create the raw, unsigned transaction that contains all metadata 
    needed to transact
    Args:
        coin (str): The coin type defined in constants.py
        account (obj): The account object from priv_key_to_account()
        to (str): The recipient address
        amount (flt): The amount of the coin to send
    Returns:
        A dictionary of values: to, from, value, gas, gasPrice, nonce and chainID
    """
    # check the coin for ETH
    if coin == ETH:
        # estimate gas price for transaction
        gasEstimate = connection.eth.estimateGas({
            "from": account.address,
            "to": to,
            "value": amount
        })
        # return necessary data for transaction
        return {
            'chainId': 999,
            'to': to,
            'from': account.address,
            'value': amount,
            'gas': gasEstimate,
            'gasPrice': connection.eth.gasPrice,
            'nonce': connection.eth.getTransactionCount(account.address)
        }
    # check the coin for BTCTEST
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to.address, amount, BTC)])

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):
    """This will call create_tx, sign the transaction, then send it to the designated network.
    needed to transact
    Args:
        coin (str): The coin type defined in constants.py
        account (obj): The account object from priv_key_to_account()
        to (str): The recipient address
        amount (flt): The amount of the coin to send
    Returns:
        Sent transaction status
    """
    # create raw transaction
    raw_tx = create_tx(coin, account, to, amount)
    # sign the raw transaction
    signed = account.sign_transaction(raw_tx)

    # check the coin for ETH
    if coin == ETH:
        # send raw transaction    
        return connection.eth.sendRawTransaction(signed.rawTransaction)

    # check the coin for BTCTEST
    if coin == BTCTEST:
        # send raw transaction    
        return NetworkAPI.broadcast_tx_testnet(signed)



