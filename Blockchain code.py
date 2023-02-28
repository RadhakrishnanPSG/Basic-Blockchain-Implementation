import datetime
import hashlib
import json
from flask import Flask,jsonify

class Blockchain:
    def __init__(self):
        self.chain=[]
        self.create_block(proof = 1,prev = '0')
        
    def create_block(self,proof,prev):
        block = {
                'index' : len(self.chain)+1,
                'timestamp' : str(datetime.datetime.now()),
                'proof' : proof,
                'prev' : prev
            }
        self.chain.append(block)
        return block
    
    def get_prev(self):
        return self.chain[-1]
    
    def proof_of_work(self,prev_proof):
        new_proof = 1
        check_proof = False
        while not check_proof:
            #my own logic for hash
            hash_val = hashlib.sha256(str(new_proof**2-prev_proof**2).encode()).hexdigest()
            #my own logic for hash starting with 4 zeroes
            if hash_val[:4]=='0000':
                check_proof = True
            else:
                new_proof+=1
        return new_proof
    
    def hash(self,block):
        encoded_dump = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_dump).hexdigest()
    
    def is_chain_valid(self,chain):
        prev_block = chain[0]
        block_index = 1
        while block_index<len(chain):
            block = chain[block_index]
            if block['prev'] != self.hash(prev_block):
                return False
            prev_proof = prev_block['proof']
            proof = block['proof']
            hash_val = hashlib.sha256(str(proof**2-prev_proof**2).encode()).hexdigest()
            if hash_val[:4]!='0000':
                return False
            prev_block = block
            block_index+=1
        return True
    
#Flask component

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

blockchain = Blockchain()
#mining component

@app.route('/mine_block',methods = ['GET'])
def mine_block():
    prev_blk = blockchain.get_prev()
    prev_proof = prev_blk['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_blk)
    block = blockchain.create_block(proof, prev_hash)
    response = {'index': block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'prev':block['prev']}
    return jsonify(response), 200

@app.route('/get_chain',methods = ["GET"])
def get_chain():
    response = {'chain':blockchain.chain,
                'length':len(blockchain.chain)}
    return jsonify(response), 200

@app.route('/is_valid',methods = ['GET'])
def is_valid():
    val = blockchain.is_chain_valid(blockchain.chain)
    if val:
        response = {'msg' : 'VALID'}
    else:
        response = {'msg' : 'INVALID'}
    return jsonify(response), 200

#run the app
app.run(host = '0.0.0.0',port = 5000)

