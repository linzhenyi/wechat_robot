# env

**基于cixingguangming55555的wechat机器人做的简单的python封装，https://github.com/cixingguangming55555/wechat-bot**

**python版本为3.9.1 64位**

# 部分模块需要你自己改写一下

authority_cfg.py中，涉及config\authority_cfg.json需要自己修改一下wechat机器人(self)和超级管理者(super_admin)等的wechat id，形如wxid_xxxxxxxx。该模块主要用来划分和控制机器人的一部分功能权限。wechat id可使用wx_data模块获取到。

chatgpt模块需要安装openai的库，之后修改openai.api_key参数填入你自己的chatgpt的key

test模块主要便于你开发过程中编写调试自己的代码，其中保留了我部分的调试代码，需要用的话要自己改一下

