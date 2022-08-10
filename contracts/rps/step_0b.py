# rock paper scissors smart contract
from ast import Assert
from pyteal import *
from pyteal.ast.bytes import Bytes
from pyteal_helpers import program

def approval(): # Uses local storage, not global storage
    #locals
    local_opponent = Bytes("opponent")  #Byteslice #would store opponent account address
    local_wager = Bytes("wager") #uint64
    local_commitment = Bytes("commitment") #Byteslice #hashed play
    local_reveal = Bytes("reveal") #byteslice #unhashed play 

    #operations
    op_challenge = Bytes("challenge")
    op_accept = Bytes("accept")
    op_reveal = Bytes("reveal")
    
    @Subroutine (TealType.none) #subroutines allows code reusablility in teal. This subroutine returns nothing
    def reset( account : Expr):
        return Seq(
            App.localPut(account, local_opponent , Bytes("")),
            App.localPut(account, local_wager , Int(0)),
            App.localPut(account, local_commitment , Bytes("")),
            App.localPut(account, local_reveal , Bytes("")),
        )

    @Subroutine (TealType.uint64) # Teal doesn't have booleans so integers are used instead
    def is_empty(account : Expr):
        return Return(
            And( # Makes sure all these conditions are true
                App.localGet(account, local_opponent) == Bytes(""),
                App.localGet(account, local_wager) == Int(0),
                App.localGet(account, local_commitment) == Bytes(""),
                App.localGet(account, local_reveal) == Bytes(""),
            ),
        ), # python + Pyteal returns

    @Subroutine (TealType.none)
    def create_challenge():
        return Seq(
            #would run alot of security checks & send a transaction
            program.check_self(
                group_size=Int(2),
                group_index=Int(0),
            ),
            program.check_rekey_zero(2),
            Assert(
                And(
                    # Check wager payment transaction
                    Gtxn[1].type_enum() == TxnType.Payment, 
                    Gtxn[1].receiver() == Global.curent_application_address(),
                    Gtxn[1].close_remainder_to() == Global.zero_address(),

                    # Check opponent is opted into smart contract
                    App.optedIn(Txn.accounts[1], Global.curent_application_id()),

                    # Check to make sure that both accounts are available to play
                    is_empty(Txn.sender()),
                    is_empty(Txn.accounts[1]),

                    # Check for commitment
                    Txn.application_args.length() == Int(2), # ensures it exists
                )  
            ),
            App.localPut(Txn.sender(), local_opponent, Txn.accounts[1]),
            App.localPut(Txn.sender(), local_wager, Gtxn[1].amount()),
            App.localPut(Txn.sender(), local_commitment, Txn.application_args[1]),
            Approve(),

        )
    
    @Subroutine (TealType.none)
    def accept_challenge():
        return Reject()

    @Subroutine (TealType.none)
    def reveal():
        return Reject()

    return program.event (
        init=Approve(),
        opt_in = Seq (
            reset(Int(0)),
            Approve(),
        ),

        no_op=Seq(
            Cond(
                [Txn.application_args[0] == op_challenge, create_challenge()],
                [Txn.application_args[0] == op_accept, accept_challenge()],
                [Txn.application_args[0] == op_reveal, reveal()],
            ),
            Reject(),
        ),

    )
    

def clear():
    return Approve()