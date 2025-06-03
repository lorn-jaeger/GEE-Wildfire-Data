"""

Google Earth has an export limit of 3000. When querrying a large amount of fires, this problem breaks down the pipeline. I need to maintain my own export queue to solve this issue.
"""

from ee_wildfire.constants import EXPORT_QUEUE_SIZE

class CircleQueue:

    def __init__(self, userConfig):
        self.userConfig = userConfig
        self.maxSize = EXPORT_QUEUE_SIZE
        self.queueList = [0] * self.maxSize

        self.front = -1
        self.rear = -1

    def __str__(self) -> str:
        return str(self.queueList)

    def _handle_full_queue(self):
        print("QUEUE FULL")

    def _handle_empty_queue(self):
        print("QUEUE EMPTY")


    def enqueue(self, item):
        if self.isEmpty():
            self.front = 0
            self.rear = 0
            self.queueList[self.rear] = item
        else:
            self.rear = (self.rear + 1) % self.maxSize
            if self.rear == self.front:
                self.rear = (self.rear - 1 + self.maxSize) % self.maxSize
                self._handle_full_queue()

            else:
                self.queueList[self.rear] = item

    def dequeue(self):
        item = -1

        if not self.isEmpty():
            item = self.queueList[self.front]
            if self.front == self.rear:
                self.front = -1
                self.rear = -1
            else:
                self.front = (self.front + 1) % self.maxSize

        else:
            self._handle_empty_queue()

        return item

    def dequeueItem(self, item):
        if self.isEmpty():
            self._handle_empty_queue()
            return None

        try:
            itemIndex = self.queueList.index(item, self.front, self.rear+1 if self.rear >= self.front else self.maxSize)

        except ValueError:
            # item not found
            return None


        # remove item by shifting all elements after it to the left
        i = itemIndex
        while i != self.rear:
            next_i = (i+1)%self.maxSize
            self.queueList[i] = self.queueList[next_i]
            i = next_i

        # clear up old rear item
        self.queueList[self.rear] = 0

        if(self.rear == self.front):
            # queue becomes empty
            self.front = -1
            self.rear = -1

        else:
            self.rear = (self.rear - 1 + self.maxSize) % self.maxSize


    
    def peek(self):
        if not self.isEmpty():
            return self.queueList[self.front]
        else:
            self._handle_empty_queue()
            return -1

    def isEmpty(self):
        return self.front == -1 and self.rear == -1

    def isFull(self):
        if not self.isEmpty():
            cond1 = (self.rear + 1) % self.maxSize == self.front
            cond2 = (self.front == 0) and self.rear == self.maxSize - 1
            return cond1 or cond2

    def refreshExports(self):

        for item in self.queueList:
            files, _ = self.userConfig.downloader.get_files_in_drive()
            if item in files:
                self.dequeueItem(item)



def main():
    from ee_wildfire.UserConfig.UserConfig import UserConfig
    uf = UserConfig()
    q = CircleQueue(uf)
    print(q.isEmpty())

    for i in range(0,4):
        q.enqueue(i)

    print(q.isFull())

if __name__ == "__main__":
    main()
