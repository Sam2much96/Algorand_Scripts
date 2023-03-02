![Screenshot](https://github.com/Sam2much96/algorand_python_Scripts/blob/main/contracts/escrow/Box_Escrow_Logo.png)

**Demo Video**

[![Demo video](https://img.youtube.com/vi/BPCMQdgbb3M/hqdefault.jpg)](https://youtu.be/BPCMQdgbb3M)

# How to Use:
 
 **Run the Script in Python**
   ```
  $python3 Box_storage_escrow_3.py
  ```
  
  **Type in the command you wish being performed. Any other command would throw an error.**
  ```
  $ Enter command  [deploy,pay,withdraw,deposit,mint,method_call,balance, delete ]
  ```

**Run the Shell Command in Sandbox Environment.**

  ```
  $ goal app method --arg "1" --arg "47K35YGGZQWMRL4QJ3C7SLYBIA4U2QM2OP523IJH27JJWN573ZI3Z3AMXM" --method "withdraw(uint64,account)void" --fee 2000 --app-id 7 --from WOSFDOS3DRD7UAHBJH3LA2PTZKJMVHU2STVDUXNSCKMVRDGNZHTNIEHUJY
  ```

Where "withdraw(uint64, account)void" is the Withdrawal Method's Signature. This is used in constructing Atomic Transactions with ABI method calls in Algonaut's Rust Crate Implementation.


# Box Escrow:
 
 It's an Arc 4 Escrow Smart Contract that utilizes Box Storage for storing withdrawal information from the smart contract, Checking User's Wallet Balance and Minting NFT's to Wallet Addresses via NoOp Application call Txns & Optin Application Call Txns.

##  Features

**(1) Box Storage** 


**(2) Escrow Withdrawals**


**(3) Escrow Deposits**


**(4) Mints NFTs Assets**

**(5) Debugs Teal Coding Teal Inspector**

**(6) L1 Algorand Transaction Logic all implemented in one script, Update, Delete, Deploy and Call App Methods**

