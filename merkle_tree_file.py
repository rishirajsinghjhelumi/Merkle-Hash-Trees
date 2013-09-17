import os
import sys
import math
import socket
import hashlib

NUM_CHUNKS = 16
merkleTrees = {}

class MerkleTree:

	def __init__(self,fileName):

		self.fileName = fileName
		self.fileDescriptor = open(self.fileName)
		self.fileSize = self.getFileSize()
		self.numChunks = NUM_CHUNKS
		self.chunkSize = self.fileSize / self.numChunks + (1 if self.fileSize % self.numChunks != 0 else 0)
		self.fileChunks = self.getFileChunks()

		self.treeHeight = self.getTreeHeight()
		self.numNodes = ( 1<<(self.treeHeight + 1) ) - 1
		self.tree = ["" for i in xrange(self.numNodes + 1)]

		self.createTree()

	def createTree(self):

		offset = 1 << self.treeHeight
		index = 0
		for chunk in self.fileChunks:
			self.tree[offset + index] = self.getHash(chunk)
			index = index + 1

		for i in xrange(self.treeHeight-1,-1,-1):
			offset = 1 << i
			for j in xrange(1<<i):
				index = offset + j
				leftChildHash , rightChildHash = self.tree[index<<1] , self.tree[(index<<1) + 1]
				nodeKey = leftChildHash + rightChildHash
				self.tree[index] = self.getHash(nodeKey)

	def updateTree(self):

		self.fileDescriptor = open(self.fileName)
		self.fileSize = self.getFileSize()
		self.chunkSize = self.fileSize / self.numChunks + (1 if self.fileSize % self.numChunks != 0 else 0)
		
		fileChunks = self.getFileChunks()
		offset = 1 << self.treeHeight
		index = 0
		changedChunks = []
		for chunk in fileChunks:
			newHash = self.getHash(chunk)
			if newHash != self.tree[offset + index]:
				self.updateChunk(offset + index,newHash)
				changedChunks.append(index)
			index = index + 1

		return changedChunks

	def updateChunk(self,index,newHash):

		self.tree[index] = newHash
		if index % 2 == 0:
			leftChildHash , rightChildHash = self.tree[index] , self.tree[index + 1]
		else:
			leftChildHash , rightChildHash = self.tree[index - 1] , self.tree[index]

		index = index >> 1
		while index:
			nodeKey = leftChildHash + rightChildHash
			self.tree[index] = self.getHash(nodeKey)
			if index % 2 == 0:
				leftChildHash , rightChildHash = self.tree[index] , self.tree[index + 1]
			else:
				leftChildHash , rightChildHash = self.tree[index - 1] , self.tree[index]
			index = index >> 1

	def getSibling(self,index):

		if index % 2 == 0:
			return index + 1
		else:
			return index - 1

	def getUncles(self,index):

		uncles = []

		index = index >> 1
		while index != 1:
			if index % 2 == 0:
				uncles.append(index + 1)
			else:
				uncles.append(index - 1)
			index = index >> 1

		return uncles

	def getRootHash(self):

		return self.tree[1]

	def getTreeHeight(self):

		return int(math.log(self.numChunks) / math.log(2))

	def getHash(self,key):

		hashVal = hashlib.sha256(key).hexdigest()
		return hashVal

	def getFileSize(self):

		size = os.stat(self.fileName).st_size
		return size

	def getFileChunks(self):

		while True:
			data = self.fileDescriptor.read(self.chunkSize)
			if not data:
				self.fileDescriptor.close()
				break
			yield data

	def getNthChunk(self,n):

		fileDescriptor = open(self.fileName)
		seekIndex = n * self.chunkSize
		fileDescriptor.seek(seekIndex)
		data = fileDescriptor.read(self.chunkSize)
		fileDescriptor.close()

		return data

def compareMerkleTrees(tree1 , tree2 , index):

	offset = 1 << tree1.treeHeight
	if index >= offset and index < 2 * offset:
		if tree1.tree[index] != tree2.tree[index]:
			return [index - offset]
		else:
			return []
	if tree1.tree[index] == tree2.tree[index]:
		return []
	else:
		return compareMerkleTrees(tree1,tree2,index<<1) + compareMerkleTrees(tree1,tree2,(index<<1) + 1)


def runScan():

	while True:

		command = raw_input().split()
		if command[0] == 'exit':
			sys.exit(0)

		elif command[0] == 'read':
			try:
				fileName = command[1]
			except:
				print 'Supply file name....'
				continue
			try:
				open(fileName)
			except:
				print 'File dont exist....'
				continue
			if fileName in merkleTrees:
				print 'Merkle Tree previously calculated for this file.... Run update....'
				continue
			merkleTrees[fileName] = MerkleTree(fileName)
			print "Done...."

		elif command[0] == 'update':
			try:
				fileName = command[1]
			except:
				print 'Supply file name....'
				continue
			try:
				open(fileName)
			except:
				print 'File dont exist....'
				continue
			if fileName not in merkleTrees:
				print 'Merkle Tree not created for this file....'
				continue
			print merkleTrees[fileName].updateTree()

		elif command[0] == 'compare':
			try:
				fileName1 , fileName2 = command[1] , command[2]
			except:
				print 'Supply 2 file names to compare....'
				continue
			try:
				open(fileName1)
				open(fileName2)
			except:
				print 'File dont exist(s)....'
				continue
			if fileName1 not in merkleTrees or fileName2 not in merkleTrees:
				print 'Merkle Tree not created for this file(s)....'
				continue
			print compareMerkleTrees(merkleTrees[fileName1],merkleTrees[fileName2],1)

		else:
			print 'Bad Input....'

if __name__ == '__main__':

	runScan()