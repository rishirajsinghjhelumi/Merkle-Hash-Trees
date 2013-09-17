import random
import string

numFiles = 8

folderPath = '.'

def getRandom(N):
		return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))

for i in range(numFiles):
		fileName = folderPath + "/" + "test" + str(i) + ".random"
		f = open(fileName,'w')
		numChars = random.randint(1024,2048)
		f.write(getRandom(numChars))
		f.close()

