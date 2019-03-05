# mnist
identify numbers
用户在本地用curl命令提交数字图片文件，在cassandra页面下得到文件名、识别出的数字和时间信息。

前期准备：
在已经有cassandra镜像前提下，用docker run --name xu-cassandra -p 9042:9042 -d cassandra 方式启动容器，
并用docker exec -it xu-cassandra cqlsh 指令进入容器cqlsh界面。

具体过程：
首先，在终端用命令进入本地的Dockerfile.txt和requirements.txt目录中，用指令docker buid -t python3-tensorflow 构建镜像。
接着用docker run -it --name python3-tensorflow --link xu-cassandra:cassandra -p 4000:80 python3-tensorflow 指令启动容器python3-tensorflow,
使该容器与xu-cassandra容器相连，并且使该容器的80端口能被本地4000端口访问。

其次，用以下命令将本地的mnist_deep.py、test.py和app.py文件上传到python3-tensorflow容器中。
docker inspect -f '{{.ID}}' python3-tensorflow  得到容器长ID
docker cp 本地文件路径如/home/.../test.py 上一步得到的容器长ID:文件放在容器中路径如/root/mnist/test.py
最好把几个.py文件放在容器的一个文件夹里，我放在/root/mnist文件夹下

建立模型：
sudo docker exec -it 容器ID bash 进入python3-tensorflow容器中
用cd命令进入保存有上一步几个.py文件的文件夹中
python3 mnist_deep.py 运行该文件，会有自动下载的data_set文件夹，里面是训练集，还有几个其他文件。
到此，模型就建好了。

识别图片：
python3 app.py 将运行图片识别的程序，在本地终端cd命令进入图片存储的文件夹，然后输入curl localhost:4000/upload -F "file=@图片名称“ 上传图片
识别结果会被返回
在cassandra容器中，输入以下命令：
use xukeyspace;
select * from xutable;
就能得到上传图片名称、识别结果和时间信息。
