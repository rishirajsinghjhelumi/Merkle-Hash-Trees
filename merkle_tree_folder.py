import os
import sys
import math
import socket
import hashlib

merkleTrees = {}

class MerkleTree:

	def __init__(self,fileName):

		self.folderName = fileName
		self.numFiles = self.getNumFiles()
		self.files = self.getFiles()
		self.fileDict = {}

		self.treeHeight = self.getTreeHeight()
		self.numNodes = ( 1<<(self.treeHeight + 1) ) - 1
		self.tree = ["" for i in xrange(self.numNodes + 1)]

		self.createTree()

	def createTree(self):

		offset = 1 << self.treeHeight
		index = 0
		for File in self.files:
			chunk = self.getFileData(File)
			self.fileDict[index] = File
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
		
		files = self.getFiles()
		offset = 1 << self.treeHeight
		index = 0
		changedChunks = []
		for File in files:
			chunk = self.getFileData(File)
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

		height = int(math.log(self.numFiles) / math.log(2)) + 1
		if self.numFiles & (self.numFiles - 1) == 0:
			height = height - 1
		return height

	def getHash(self,key):

		hashVal = hashlib.sha256(key).hexdigest()
		return hashVal

	def getFileSize(self):

		size = os.stat(self.folderName).st_size
		return size

	def getFileData(self,fileName):

		fileDescriptor = open(os.path.join(self.folderName,fileName))
		data = fileDescriptor.read()
		fileDescriptor.close()
		return data

	def getFiles(self):

		files = os.walk(self.folderName).next()[2]
		return files

	def getNumFiles(self):

		files = os.walk(self.folderName).next()[2]
		return len(files)

	def getNthChunk(self,n):

		fileDescriptor = open(self.folderName)
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
				print 'Supply folder name....'
				continue
			if os.path.isdir(fileName) == False:
				print 'Folder dont exist....'
				continue
			if fileName in merkleTrees:
				print 'Merkle Tree previously calculated for this folder.... Run update....'
				continue
			merkleTrees[fileName] = MerkleTree(fileName)
			print "Done...."

		elif command[0] == 'update':
			try:
				fileName = command[1]
			except:
				print 'Supply folder name....'
				continue
			if os.path.isdir(fileName) == False:
				print 'Folder dont exist....'
				continue
			if fileName not in merkleTrees:
				print 'Merkle Tree not created for this folder....'
				continue
			filesIndex = merkleTrees[fileName].updateTree()
			if len(filesIndex) == 0:
				print "No file Updated ...."
				continue
			print "Changed Files :"
			for index in filesIndex:
				print "\t" + merkleTrees[fileName].fileDict[index]

		elif command[0] == 'compare':
			try:
				fileName1 , fileName2 = command[1] , command[2]
			except:
				print 'Supply 2 folder names to compare....'
				continue
			if os.path.isdir(fileName1) == False or os.path.isdir(fileName2) == False:
				print 'Folder(s) dont exist....'
				continue
			if fileName1 not in merkleTrees or fileName2 not in merkleTrees:
				print 'Merkle Tree not created for this folder(s)....'
				continue
			filesIndex = compareMerkleTrees(merkleTrees[fileName1],merkleTrees[fileName2],1)
			if len(filesIndex) == 0:
				print "All files Match ...."
				continue
			print "Different Files :"
			for index in filesIndex:
				print "\t" + merkleTrees[fileName].fileDict[index]

		elif command[0] == 'send':
			try:
				fileName1 , fileName2 = command[1] , command[2]
			except:
				print 'Supply server and client folder names to send data from server to client....'
				continue
			if os.path.isdir(fileName1) == False or os.path.isdir(fileName2) == False:
				print 'Folder(s) dont exist....'
				continue
			if fileName1 not in merkleTrees or fileName2 not in merkleTrees:
				print 'Merkle Tree not created for this folder(s)....'
				continue
			filesIndex = compareMerkleTrees(merkleTrees[fileName1],merkleTrees[fileName2],1)
			if len(filesIndex) == 0:
				print "Nothing to Send...."
				continue 
			for index in filesIndex:
				filePathServer = os.path.join(fileName1,merkleTrees[fileName1].fileDict[index])
				filePathClient = os.path.join(fileName2,merkleTrees[fileName2].fileDict[index])
				print "\t Sending %s ...."%merkleTrees[fileName1].fileDict[index]
				os.system("cp %s %s"%(filePathServer,filePathClient))

			merkleTrees[fileName2].updateTree()
			print "Client Updated...."

		else:
			print 'Bad Input....'

if __name__ == '__main__':

	runScan()