# 区域数字经济发展指数
## 命令
### 安装依赖环境
```bash
./install.bat
```

### 运行
```bash
./run.bat
```
1. 激活环境 
2. 安装python依赖包
3. 收集静态文件
4. 运行项目

### 运行环境重启
```bash
./runtime.bat
```
只能在部署服务器上运行

### 其他命令
见`./commands.bat`文件

## 项目内容
1. 三张表
2. 数字经济的关键字库
3. 系统主要功能
   1. 数据收集
      1. 四个数据维度(?)
      2. 基础数据支持批量代入
      3. 网站数据周期性更新
   2. 基础查询
   3. 数据处理（更新最终评价数据）
   4. 关键词库的管理（知识图谱的展现）
   5. 各地区的发展情况
   6. 各评价维度各地区的发展情况
   7. 各地区的词云图（各地区关键词—知识图谱？）

# TODO
- [ ] 头条爬虫时间读取
  - [x] 读取并判断时间
  - [ ] 建表存储时间
- [ ] 分词函数
  - [x] 完成代码
  - [ ] 运行


# Git
## Git 工作流
1. 从远程仓库拉取master最新代码
2. rebase到dev分支上
3. 在dev分支新建自己的分支(如feature/aaa，bugfix/bbb等)
4. 将分支merge --squash到dev分支上
5. 将dev分支推送到远程仓库
6. 在远程仓库上发起pull request


## Git Commit Message 规范
```
<type>(<scope>): <subject>
<body>
<footer>
```

大致分为三个部分(使用空行分割):

标题行: 必填, 描述主要修改类型和内容

主题内容: 描述为什么修改, 做了什么样的修改, 以及开发的思路等等

页脚注释: 放 Breaking Changes 或 Closed Issues

---
1. `type`

   commit 的类型：
   1. `feat`: 新功能、新特性
   2. `fix`: 修改 bug
   3. `perf`: 更改代码，以提高性能（在不影响代码内部行为的前提下，对程序性能进行优化）
   4. `refactor`: 代码重构（重构，在不影响代码内部行为、功能下的代码修改）
   5. `docs`: 文档修改
   6. `style`: 代码格式修改, 注意不是 css 修改（例如分号修改）
   7. `test`: 测试用例新增、修改
   8. `build`: 影响项目构建或依赖项修改
   9. `revert`: 恢复上一次提交
   10. `ci`: 持续集成相关文件修改
   11. `chore`: 其他修改（不在上述类型中的修改）
   12. `release`: 发布新版本
   13. `workflow`: 工作流相关文件修改


2. `scope`

   commit 影响的范围, 比如: `route`, `component`, `utils`, `build`...


3. `subject`

   commit 的概述


4. `body`

   commit 具体修改内容, 可以分为多行.


5. `footer`

   一些备注, 通常是 BREAKING CHANGE 或修复的 bug 的链接.


