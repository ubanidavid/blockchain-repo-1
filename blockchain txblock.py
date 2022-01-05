#TxBlock
from BlockChain import CBlock
from Signatures import generate_keys, sign, verify
from Transactions import Tx
import pickle
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import random
from cryptography.hazmat.primitives import hashes
import time

reward = 25.0
leading_zeros = 2
next_char_limit = 255

class TxBlock (CBlock):
    nonce = "AAAAAAA"
    def __init__(self, previousBlock):
        super(TxBlock, self).__init__([], previousBlock)
    def addTx(self, Tx_in):
        self.data.append(Tx_in)
    def removeTx(self, Tx_in):
        try:
            self.data.remove(Tx_in)
        except:
            return False
        return True
    def check_size(self):
        savePrev = self.previousBlock
        self.previousBlock = None
        if len(pickle.dumps(self)) > 10000:
            self.previousBlock = savePrev
            return False
        self.previousBlock = savePrev
        return True
            
    def count_totals(self):
        total_in = 0
        total_out = 0
        for tx in self.data:
            for addr, amt, inx in tx.inputs:
                total_in = total_in + amt
            for addr, amt in tx.outputs:
                total_out = total_out + amt
        return total_in, total_out
    def is_valid(self):
        if not super(TxBlock, self).is_valid():
            print ("CBlock.is_valid returned False")
            return False
        spends={}
        for tx in self.data:
            if not tx.is_valid():
                print ("Tx invalid")
                print (tx)
                return False
            for addr,amt,inx in tx.inputs:
                if not addr in spends:
                    spends[addr] = amt
                else:
                    spends[addr] = spends[addr] + amt
                if not inx-1 == getLastTxIndex(addr,self.previousBlock):
                    found = False
                    count = 0
                    for tx2 in self.data:
                        for addr2,amt2,inx2 in tx2.inputs:
                            if addr == addr2 and inx2 == inx-1:
                                found=True
                            if addr == addr2 and inx2 == inx:
                                count = count + 1
                    if not found or count > 1:
                        print("Tx index out of order")
                        return False
            for addr,amt in tx.outputs:
                if not addr in spends:
                    spends[addr] = -amt
                else:
                    spends[addr] = spends[addr] - amt
        for addr in spends:
            if self.previousBlock == None:
                if spends[addr] > 0:
                    print("Can't spend in root block")
                    return False
            if spends[addr] - getBalance(addr,self.previousBlock) > 0.0000000001:
                print("Overspend for addr: " + str(addr))
                return False
        total_in, total_out = self.count_totals()
        if total_out - total_in - reward > 0.000000000001:
            return False
        if not self.check_size():
            return False
        return True
    def good_nonce(self):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(str(self.data),'utf8'))
        digest.update(bytes(str(self.previousHash),'utf8'))
        digest.update(bytes(str(self.nonce),'utf8'))
        this_hash = digest.finalize()
       
        if this_hash[:leading_zeros] != bytes(''.join([ '\x4f' for i in range(leading_zeros)]),'utf8'):
            return False
        return int(this_hash[leading_zeros]) < next_char_limit
    def find_nonce(self,n_tries=1000000):
        for i in range(n_tries):
            self.nonce = ''.join([ 
                   chr(random.randint(0,255)) for i in range(10*leading_zeros)])
            if self.good_nonce():
                return self.nonce  
        return None
def getBalance(pu_key,head_block):
    this_block = head_block
    bal = 0.0
    while this_block != None:
        for tx in this_block.data:
            for addr,amt,inx in tx.inputs:
                if addr == pu_key:
                    bal = bal - amt
            for addr,amt in tx.outputs:
                if addr == pu_key:
                    bal = bal + amt
        this_block = this_block.previousBlock
    return bal


def getLastTxIndex(pu_key,head_block):
    this_block = head_block
    index = -1
    while this_block != None:
        for tx in this_block.data:
            for addr,amt,inx in tx.inputs:
                if addr == pu_key and inx > index:
                    index = inx
        if index != -1:
            break
        this_block = this_block.previousBlock
    return index


def findLongestBlockchain(head_blocks):
    longest = -1
    long_head = None
    for b in head_blocks:
        current = b
        this_len = 0
        while current != None:
            this_len = this_len + 1
            current = current.previousBlock
        if this_len > longest:
            long_head = b
            longest = this_len
    return long_head

def saveBlocks(block_list, filename):
    fp = open(filename, "wb")
    pickle.dump(block_list, fp)
    fp.close()
    return True

def loadBlocks(filename):
    fin = open(filename, "rb")
    ret = pickle.load(fin)
    fin.close()
    return ret

if __name__ == "__main__":
    pr1, pu1 = generate_keys()
    pr2, pu2 = generate_keys()
    pr3, pu3 = generate_keys()

    pu_indeces = {}
    
    def indexed_input(Tx_inout, public_key, amt, index_map):
        if not public_key in index_map:
            index_map[public_key] = 0            
        Tx_inout.add_input(public_key, amt, index_map[public_key])
        index_map[public_key] = index_map[public_key] + 1
    

    Tx1 = Tx()
    indexed_input(Tx1, pu1, 1, pu_indeces)
    Tx1.add_output(pu2, 1)
    Tx1.sign(pr1)

    if Tx1.is_valid():
        print("Success! Tx is valid")

    savefile = open("tx.dat", "wb")
    pickle.dump(Tx1, savefile)
    savefile.close()

    loadfile = open("tx.dat", "rb")
    newTx = pickle.load(loadfile)

    if newTx.is_valid():
        print("Sucess! Loaded tx is valid")
    loadfile.close()

    root = TxBlock(None)
    root.addTx(Tx1)
    Txmine = Tx()
    Txmine.add_output(pu1,8.0)
    root.addTx(Txmine)
    Txmine = Tx()
    Txmine.add_output(pu2,8.0)
    root.addTx(Txmine)
    Txmine = Tx()
    Txmine.add_output(pu3,8.0)
    root.addTx(Txmine)

    Tx2 = Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indeces)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    root.addTx(Tx2)

    B1 = TxBlock(root)
    Tx3 = Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indeces)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    B1.addTx(Tx3)
    
    Tx4 = Tx()
    indexed_input(Tx4, pu1, 1, pu_indeces)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B1.addTx(Tx4)
    start = time.time()
    print(B1.find_nonce())
    elapsed = time.time() - start
    print("elapsed time: " + str(elapsed) + " s.")
    if elapsed < 60:
        print("ERROR! Mining is too fast")
    if B1.good_nonce():
        print("Success! Nonce is good!")
    else:
        print("ERROR! Bad nonce")
    

    savefile = open("block.dat", "wb")
    pickle.dump(B1, savefile)
    savefile.close()

    loadfile = open("block.dat" ,"rb")
    load_B1 = pickle.load(loadfile)

    for b in [root, B1, load_B1, load_B1.previousBlock]:
        if b.is_valid():
            print ("Success! Valid block")
        else:
            print ("ERROR! Bad block")

    if B1.good_nonce():
        print("Success! Nonce is good after save and load!")
    else:
        print("ERROR! Bad nonce after load")
    B2 = TxBlock(B1)
    Tx5 = Tx()
    indexed_input(Tx5, pu3, 1, pu_indeces)
    Tx5.add_output(pu1, 100)
    Tx5.sign(pr3)
    B2.addTx(Tx5)

    load_B1.previousBlock.addTx(Tx4)
    for b in [B2, load_B1]:
        if b.is_valid():
            print ("ERROR! Bad block verified.")
        else:
            print ("Success! Bad blocks detected")

    # Test mining rewards and tx fees
    pr4, pu4 = generate_keys()
    B3 = TxBlock(B2)
    Tx2 = Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indeces)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3 = Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indeces)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4 = Tx()
    indexed_input(Tx4, pu1, 1, pu_indeces)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B3.addTx(Tx2)
    B3.addTx(Tx3)
    B3.addTx(Tx4)
    Tx6 = Tx()
    Tx6.add_output(pu4,25)
    B3.addTx(Tx6)
    if B3.is_valid():
        print ("Success! Block reward succeeds")
    else:
        print("ERROR! Block reward fail")

    B4 = TxBlock(B3)
    Tx2 = Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indeces)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3 = Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indeces)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4 = Tx()
    indexed_input(Tx4, pu1, 1, pu_indeces)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B4.addTx(Tx2)
    B4.addTx(Tx3)
    B4.addTx(Tx4)
    Tx7 = Tx()
    Tx7.add_output(pu4,25.2)
    B4.addTx(Tx7)
    if B4.is_valid():
        print ("Success! Tx fees succeeds")
    else:
        print("ERROR! Tx fees fail")

    #Greedy miner
    B5 = TxBlock(B4)
    Tx2 = Tx()
    indexed_input(Tx2, pu2, 1.1, pu_indeces)
    Tx2.add_output(pu3, 1)
    Tx2.sign(pr2)
    Tx3 = Tx()
    indexed_input(Tx3, pu3, 1.1, pu_indeces)
    Tx3.add_output(pu1, 1)
    Tx3.sign(pr3)
    Tx4 = Tx()
    indexed_input(Tx4, pu1, 1, pu_indeces)
    Tx4.add_output(pu2, 1)
    Tx4.add_reqd(pu3)
    Tx4.sign(pr1)
    Tx4.sign(pr3)
    B5.addTx(Tx2)
    B5.addTx(Tx3)
    B5.addTx(Tx4)
    Tx8 = Tx()
    Tx8.add_output(pu4,26.2)
    B5.addTx(Tx8)
    if not B5.is_valid():
        print ("Success! Greedy miner detected")
    else:
        print("ERROR! Greedy miner not detected")

    print("pu4 bal:")
    print(getBalance(pu4,B5))
    B6 = TxBlock(B5)
    lastpr = pr4
    lastpu = pu4
    lastval = 3.789
    for i in range(20):
        newpr, newpu = generate_keys()
        newTx = Tx()
        indexed_input(newTx, lastpu, lastval, pu_indeces)
        newTx.add_output(newpu,lastval-0.02)
        newTx.add_output(pu4,0.02)
        newTx.sign(lastpr)
        lastpr = newpr
        lastpu = newpu
        lastval = lastval-0.02
        B6.addTx(newTx)
        savePrev = B6.previousBlock
        B6.previousBlock = None
        if len(pickle.dumps(B6)) > 10000:
            B6.previousBlock = savePrev
            if B6.is_valid():
                print("Error! Big blocks are valid")
        if len(pickle.dumps(B6)) <= 10000:
            B6.previousBlock = savePrev
            if not B6.is_valid():
                print("Error! Small blocks are invalid")
        B6.previousBlock = savePrev
    pu_indeces[pu4] = pu_indeces[pu4] - 1

    print("pu1 bal:")
    print(getBalance(pu1,B5))
    B7 = TxBlock(B5)
    Tx9 = Tx()
    indexed_input(Tx9, pu1, 25, pu_indeces)
    indexed_input(Tx9, pu1, 25, pu_indeces)
    indexed_input(Tx9, pu1, 25, pu_indeces)
    indexed_input(Tx9, pu1, 25, pu_indeces)
    indexed_input(Tx9, pu1, 25, pu_indeces)
    indexed_input(Tx9, pu1, 25, pu_indeces)
    Tx9.sign(pr1)
    B7.addTx(Tx9)
    if not B7.is_valid():
        print ("Success! Overspend detected")
    else:
        print("ERROR! Over-spend not detected")
    
    print("pu1 bal:")
    print(getBalance(pu1,B5))
    pu_indeces[pu1] = pu_indeces[pu1] - 6
    B8 = TxBlock(B5)
    Tx9 = Tx()
    indexed_input(Tx9, pu1, 30, pu_indeces)
    Tx9.add_output(pu2,30)
    Tx9.sign(pr1)
    B8.addTx(Tx9)
    Tx10 = Tx()
    indexed_input(Tx10, pu1, 30, pu_indeces)
    Tx10.add_output(pu2,30)
    Tx10.sign(pr1)
    B8.addTx(Tx10)
    Tx11 = Tx()
    indexed_input(Tx11, pu1, 30, pu_indeces)
    Tx11.add_output(pu2,30)
    Tx11.sign(pr1)
    B8.addTx(Tx11)
    Tx12 = Tx()
    indexed_input(Tx12, pu1, 30, pu_indeces)
    Tx12.add_output(pu2,30)
    Tx12.sign(pr1)
    B8.addTx(Tx12)
    if not B8.is_valid():
        print ("Success! Overspend detected")
    else:
        print("ERROR! Over-spend not detected")
     
    

    
        
        
    


    

    

    
    
