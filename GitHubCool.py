import json
import re
import subprocess
import sys
import threading

import requests
from tqdm import tqdm

local_flag = False

threadLock = threading.Lock()

# 全局变量最快ip和延时
min_time = 9999
fast_ip = ""


class PingThread(threading.Thread):
    def __init__(self, ip, pbar):
        threading.Thread.__init__(self)
        self.ip = ip
        self.pbar = pbar

    def run(self):
        if sys.platform[:3] == "win":
            str_out = ["ping", self.ip]
        elif sys.platform[:5] == "linux":
            str_out = ["ping", "-c", "4", self.ip]
        elif sys.platform == "darwin":
            str_out = ["ping", "-c", "4", self.ip]
        process = subprocess.Popen(str_out, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            # print(line)

            if sys.platform[:3] == "win":
                delay_res = re.search(r'平均 = (?P<delay>[\s\S]*?)ms', line)
            elif sys.platform[:5] == "linux":
                delay_res = re.search(r'= (?P<delay>[\s\S]*?) ms', line)
            elif sys.platform == "darwin":
                delay_res = re.search(r'= (?P<delay>[\s\S]*?) ms', line)
            if delay_res is not None:
                if sys.platform[:3] == "win":
                    delay = int(delay_res.groupdict()['delay'])
                elif sys.platform[:5] == "linux":
                    delay_str = delay_res.groupdict()['delay'].split("/")[1]
                    delay = int(float(delay_str))
                elif sys.platform == "darwin":
                    delay_str = delay_res.groupdict()['delay'].split("/")[1]
                    delay = int(float(delay_str))

                global min_time
                global fast_ip
                # 获取锁，用于线程同步
                threadLock.acquire()
                if delay < min_time:
                    min_time = delay
                    fast_ip = self.ip
                # 释放锁，开启下一个线程
                threadLock.release()
        process.wait()
        # 更新进度条
        self.pbar.update(1)


def get_dict(flag):
    if flag:
        with open("hostsdata.json", 'r', encoding="utf-8") as load_f:
            load_dict = json.load(load_f)
            return load_dict
    else:
        url = "https://cdn.jsdelivr.net/gh/space9bug/GitHubCool@master/hostsdata.json"

        response = requests.request("GET", url)

        load_dict = json.loads(response.text)
        return load_dict


def test():
    big_str = ""
    # 1.获取cdn文件
    data_dict = get_dict(local_flag)

    print("\n-----------------GitHubCool beta 首次发布：2020/10/19 11:30-----------------")
    print("您可以Star和Fork我的项目：https://github.com/space9bug/GitHubCool")
    print("本项目通过优选cdn节点，修改本地hosts文件，解决Github图片或者文件无法访问、加载缓慢的问题")
    print("支持在Windows、Linux、MacOS上使用")
    print("优选cdn节点需要大约10分钟时间，请耐心等待，优选中。。。。。。")

    count = 0
    for host_item in data_dict:
        count += len(host_item["field"])
    pbar = tqdm(total=count)

    # 2.循环遍历域名集合
    for item in data_dict:
        host = item["field"]

        T_thread = []
        for i in host:
            t = PingThread(i, pbar)
            T_thread.append(t)
        T_thread_len = len(T_thread)
        for i in range(T_thread_len):
            T_thread[i].start()

        for t in T_thread:
            t.join()

        global min_time
        global fast_ip

        # 拼接相同ip的域名
        temp_str = ""
        for name_item in item["name"]:
            if fast_ip != "":
                temp_str += f'{fast_ip} {name_item}\n'
        big_str += temp_str

        # 重置
        min_time = 9999
        fast_ip = ""

    pbar.close()
    # 3.输出优选的hosts内容
    print("_________________________________分割线_____________________________________")
    print("# GitHubCool START")
    print(big_str)
    print("# GitHubCool END")
    print("_________________________________分割线_____________________________________")

    if sys.platform[:3] == "win":
        print("1.手动打开Windows系统：C:\Windows\System32\drivers\etc\hosts")
        print("2.将上面输出内容复制到文本末尾")
        print("3.CMD命令行中输入ipconfig /flushdns使配置立即生效")

        # 按任意键退出
        subprocess.call("pause", shell=True)
    elif sys.platform[:5] == "linux":
        print("1.手动打开Linux系统：/etc/hosts")
        print("2.将上面输出内容复制到文本末尾")
        print("3.Terminal终端中输入sudo rcnscd restart使配置立即生效")
    elif sys.platform == "darwin":
        print("1.手动打开MacOS系统：/etc/hosts")
        print("2.将上面输出内容复制到文本末尾")
        print("3.Terminal终端中输入sudo killall -HUP mDNSResponder使配置立即生效")


if __name__ == '__main__':
    test()
