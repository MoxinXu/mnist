FROM ubuntu:16.04
 
RUN  apt-get update
RUN  apt-get upgrade -y
 
# Install python3
RUN  apt-get install -y python3 
 
# Install pip
RUN apt-get install -y wget vim
RUN wget -O /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
RUN python3 /tmp/get-pip.py
RUN pip install --upgrade pip
 
RUN pip install -U tensorflow

# 添加文件
ADD mnist_deep.py /root/mnist/
