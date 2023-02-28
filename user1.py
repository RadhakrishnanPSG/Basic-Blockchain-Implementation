import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain:
    def __init__(self):
        self.chain=[]
        self.transactions = []
        self.create_block(proof = 1,prev = '0')
        self.nodes = set()
        
    def create_block(self,proof,prev):
        block = {
                'index' : len(self.chain)+1,
                'timestamp' : str(datetime.datetime.now()),
                'proof' : proof,
                'prev' : prev,
                'transactions' : self.transactions
            }
        self.transactions = []
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
    
    def add_transaction(self,sender,receiver,amount):
        self.transactions.append({'sender': sender,
                                  'receiver':receiver,
                                  'amount':amount})
        prev_blk = self.get_prev()
        return prev_blk['index'] + 1
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    #called from different nodes, and hence it takes no arguments
    #consensus protocol
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_len_chain = len(self.chain)
        #get chains from all nodes and find which one is the longest
        #nodes have common url and are differentiated by their port number
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length>max_len_chain and self.is_chain_valid(chain):
                    max_len_chain = length
                    longest_chain = chain
        #if longest chain was modified
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
        
#Flask component

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

#node address is needed as the miner gets a reward from the node
#generate unique id for address for node on port 5000

node_addr = str(uuid4()).replace('-', '')

blockchain = Blockchain()
#mining component

@app.route('/mine_block',methods = ['GET'])
def mine_block():
    prev_blk = blockchain.get_prev()
    prev_proof = prev_blk['proof']
    proof = blockchain.proof_of_work(prev_proof)
    prev_hash = blockchain.hash(prev_blk)
    
    blockchain.add_transaction(node_addr, 'Person1', amount = 100)
    
    block = blockchain.create_block(proof, prev_hash)
    response = {'index': block['index'],
                'timestamp':block['timestamp'],
                'proof':block['proof'],
                'prev':block['prev'],
                'transactions':block['transactions']}
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

#Adding new transaction to blockchain
@app.route("/add_transaction",methods = ["POST"])
def add_transaction():
    json_obj = request.get_json()
    required_keys = ['sender','receiver','amount']
    if not all(val in json_obj for val in required_keys):
        return "Required data missing!", 400
    index_to_add = blockchain.add_transaction(json_obj['sender'],json_obj['receiver'], json_obj['amount'])
    response = {'msg':f'Transaction added to block {index_to_add}'}
    return jsonify(response), 201

#Decentralization
#Connecting new nodes
@app.route('/connect_node',methods=["POST"])
def connect_node():
    json_obj = request.get_json()
    nodes = json_obj.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {"msg":"All nodes are now connected",
                'all_nodes':list(blockchain.nodes)}
    return jsonify(response), 201

#replacing the chain if a longer chain is found
@app.route('/is_replaced',methods = ['GET'])
def is_replaced():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'msg' : 'Chain replaced with longest chain',
                    'new_chain':blockchain.chain}
    else:
        response = {'msg' : 'Existing chain was the longest',
                    'exsiting_chain':blockchain.chain}
    return jsonify(response), 200

#run the app
app.run(host = '0.0.0.0',port = 5001)

