#Wallet
import SocketUtils
import Transactions
import TxBlock
import pickle
import Signatures

head_blocks = [None]
wallets = [('localhost',5006)]
miners = [('localhost',5005),('localhost',5007)]
break_now = False
verbose = True
my_private,my_public = Signatures.generate_keys()
tx_index = {}


def StopAll():
    global break_now
    break_now = True
def walletServer(my_addr):
    global head_blocks
    global tx_index
    try:
        head_blocks = TxBlock.loadBlocks("AllBlocks.dat")
    except:
        head_blocks = TxBlock.loadBlocks("GenesisBlock.dat")
    try:
        fp = open("tx_index.dat","rb")
        tx_index = pickle.load(fp)
        fp.close()
    except:
        tx_index = {}
    server = SocketUtils.newServerConnection('localhost',5006)
    while not break_now:
        newBlock = SocketUtils.recvObj(server)
        if isinstance(newBlock,TxBlock.TxBlock):
            TxBlock.processNewBlock(newBlock,head_blocks)
    server.close()
    TxBlock.saveBlocks(head_blocks, "AllBlocks.dat")
    fp = open("tx_index.dat","wb")
    pickle.dump(tx_index,fp)
    fp.close()
    return True
        
def getBalance(pu_key):
    long_chain = TxBlock.findLongestBlockchain(head_blocks)
    return TxBlock.getBalance(pu_key,long_chain)

def sendCoins(pu_send, amt_send, pr_send, pu_recv, amt_recv):
    global tx_index
    newTx = Transactions.Tx()
    if not pu_send in tx_index:
        tx_index[pu_send]=0
    newTx.add_input(pu_send, amt_send, tx_index[pu_send])
    newTx.add_output(pu_recv, amt_recv)
    newTx.sign(pr_send)
    for ip,port in miners:
        SocketUtils.sendObj(ip,newTx,port)
    tx_index[pu_send] = tx_index[pu_send] + 1
    return True

def WalletStart():
    #Load head_blocks, private and public keys
    #Load miner list
    #TODO load address book
    #Start walletServer
    return True

def WalletStop():
    #Save head_blocks
    #Close threads
    return True

if __name__ == "__main__":
    
    import time
    import Miner
    import threading
    import Signatures
    def Thief(my_addr):
        my_ip, my_port = my_addr
        server = SocketUtils.newServerConnection(my_ip,my_port)
        # Get Txs from wallets
        while not break_now:
            newTx = SocketUtils.recvObj(server)
            if isinstance(newTx,Transactions.Tx):
                for ip,port in miners:
                    if not (ip==my_ip and port == my_port):
                        SocketUtils.sendObj(ip,newTx,port)
                    
        
    Miner.saveTxList([],"Txs.dat")
    
    miner_pr, miner_pu = Signatures.generate_keys()
    t1 = threading.Thread(target=Miner.minerServer, args=(('localhost',5005),))
    t2 = threading.Thread(target=Miner.nonceFinder, args=(wallets, miner_pu))
    t3 = threading.Thread(target=walletServer, args=(('localhost',5006),))
    t1.start()
    t3.start()

    pr1,pu1 = Signatures.loadKeys("private.key","public.key")
    pr2,pu2 = Signatures.generate_keys()
    pr3,pu3 = Signatures.generate_keys()

    #Query balances
    bal1 = getBalance(pu1)
    print(bal1)
    bal2 = getBalance(pu2)
    bal3 = getBalance(pu3)

    #Send coins
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu2, 0.1)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)
    sendCoins(pu1, 0.1, pr1, pu3, 0.03)

    t2.start()
    time.sleep(60)

    #Save/Load all blocks
    TxBlock.saveBlocks(head_blocks, "AllBlocks.dat")
    head_blocks = TxBlock.loadBlocks("AllBlocks.dat")

    #Query balances
    new1 = getBalance(pu1)
    print(new1)
    new2 = getBalance(pu2)
    new3 = getBalance(pu3)

    #Verify balances
    if abs(new1-bal1+2.0) > 0.00000001:
        print("Error! Wrong balance for pu1")
    else:
        print("Success. Good balance for pu1")
    if abs(new2-bal2-1.0) > 0.00000001:
        print("Error! Wrong balance for pu2")
    else:
        print("Success. Good balance for pu2")
    if abs(new3-bal3-0.3) > 0.00000001:
        print("Error! Wrong balance for pu3")
    else:
        print("Success. Good balance for pu3")

    #Thief will try to duplicate transactions
    miners.append(('localhost',5007))
    t4 = threading.Thread(target=Thief,args=(('localhost',5007),))
    t4.start()
    sendCoins(pu2,0.2,pr2,pu1,0.2)
    time.sleep(20)
    #Check balances
    newnew1 = getBalance(pu1)
    print(newnew1)
    if abs(newnew1 - new1 - 0.2) > 0.000000001:
        print("Error! Duplicate Txs accepted.")
    else:
        print("Success! Duplicate Txs rejected.")
    

    Miner.StopAll()
    
    t1.join()
    t2.join()

    num_heads = len(head_blocks)
    minus_two = head_blocks[0].previousBlock.previousBlock
    newB = TxBlock.TxBlock(minus_two)
    newB.previousBlock = None
    SocketUtils.sendObj('localhost',newB,5006)
    time.sleep(4)
    if len(head_blocks) != num_heads + 1:
        print("Error! Branch block should be head")
    if head_blocks[-1].previousBlock != minus_two:
        print("Error! Branch block has wrong parent")
    
    
    StopAll()
    t3.join()

    print ("Exit successful.")
                
    



