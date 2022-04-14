[TOC]

### 环境

1. Windows10（默认编码未修改）。
2. js文件保存编码均为utf-8。
3. 本文要求先安装node，这也是pyexecjs的要求。本机node版本：`v16.13.2`。

### 初遇问题

文章链接：https://juejin.cn/post/7086404607332581383/

**作者：[hans774882968](https://blog.csdn.net/hans774882968)以及[hans774882968](https://juejin.cn/user/1464964842528888)**

参考链接3提出了python执行js的一个解决方案：pyexecjs。这个库已经停止维护了，不建议使用。pyv8、js2py也弃用。

本文的目标：**跑参考链接3的demo**。遗憾的是，在此过程中我遇到了编码问题。查阅百度知：系统默认编码和js文件保存的编码不一致，而pyexecjs生成temp文件用的是系统默认编码。

我一不想改js文件保存编码，二不想改系统默认编码（似乎会有些小麻烦）。于是试着去改了改pyexecjs源码，失败。

一筹莫展之时，我看到了参考链接2。顺着他的思路，我们为什么不用`node`命令去运行js文件，然后拿输出呢？于是我写了如下代码，试图直接从输出中拿结果（用到subprocess模块）：

```python
def demo1(goals):
    crypto_js = 'crypto.js'
    p = subprocess.Popen(
        ['node',crypto_js],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8'
    )
    res = p.communicate()[0]
    res = '\n'.join(res.split('\n')[1:])
    print(res)
    o = json.loads('{"res": %s}' % res.replace("'",'"'))
    want = o["res"]
    assert len(want) == len(goals)
    for i in range(len(want)):
        assert want[i] == goals[i]
```

这个代码虽然能跑通参考链接3的demo，但实在太丑。我又看了看pyexecjs源码，觉得其实现思路并不复杂。于是我有了这样的想法：自己实现一个微型的pyexecjs，只适配自己的开发环境，从而大大减少工作量。

### pyexecjs源码初步阅读笔记

让我们首先看看pyexecjs的用法（代码来自参考链接3）：

```python
import execjs
import json

item = {
    'name': '凯文-杜兰特',
    'image': 'durant.png',
    'birthday': '1988-09-29',
    'height': '208cm',
    'weight': '108.9KG'
}

file = 'crypto.js'
node = execjs.get()
ctx = node.compile(open(file).read())

js = f"getToken({json.dumps(item, ensure_ascii=False)})"
print(js)
result = ctx.eval(js)
print(result)
```

- `node.compile`读入上下文的代码。
- `ctx`是一个`Context`对象，`Context`在`_external_runtime.py`定义。

pyexecjs处理了多种JS引擎，但我们只查看与node有关的。

首先自然是看`__init__.py`

```python
get = execjs._runtimes.get

def compile(source, cwd=None):
    return get().compile(source, cwd)
compile.__doc__ = AbstractRuntime.compile.__doc__
```

故阅读`_runtimes.py`。发现`get()`返回的是一个`ExternalRuntime`对象。故阅读`_external_runtime.py`，不难发现它最终是通过运行`node`命令，进入交互模式（与python类似），进而执行`_runner_sources.Node`（在`_runner_sources.py`）的代码

```python
Node = r"""(function(program, execJS) { execJS(program) })(function() { #{source}
}, function(program) {
  var output;
  var print = function(string) {
    process.stdout.write('' + string + '\n');
  };
  try {
    result = program();
    print('')
    if (typeof result == 'undefined' && result !== null) {
      print('["ok"]');
    } else {
      try {
        print(JSON.stringify(['ok', result]));
      } catch (err) {
        print('["err"]');
      }
    }
  } catch (err) {
    print(JSON.stringify(['err', '' + err]));
  }
});"""
```

其中`#{source}`被替换为包含了上下文（`ctx = execjs.get().compile(open(file).read())`，对应`Context`的`self._source`）和单行表达式（`ctx.eval`的输入参数`source`）的代码。

`#{source}`生成代码的大致方式是`self._source + '\n' + return eval('(' + json.dumps(source, ensure_ascii=True) + ')')`，仅支持单行表达式。

执行完毕后，通过`_external_runtime.py`的`Context._extract_result`提取输出。

从`Context._exec_`不难看出，执行`ctx = node.compile(open(file).read())`时并未执行上下文的代码，而每次执行`ctx.eval`都要重新执行一遍上下文的代码。对此我们暂时没有优化的办法。

### 实现

已开源至[GitHub](https://github.com/Hans774882968/mypyexecjs)

`myexecjs.py`就是微型的pyexecjs，`main.py`用来完成参考链接3的demo。使用方式可参考`test.py`和`main.py`，与pyexecjs类似。

- `myexecjs.py`的`node_wrap`由`_runner_sources.Node`（在上文）改动而来，新增了对BigInt的支持。
- pyexecjs用了js的`eval`函数，且仅支持单行代码。我认为只支持单行表达式时不需要用到js的`eval`函数，详见GitHub链接（若理解有误，还请佬佬们指出~）。
- 增加了多行支持（感觉是没啥用的功能？），用`use_js_eval`选项开启。
- 原本想支持Promise，但感觉到这个任务十分困难，遂作罢。

已知的问题：

- `eval`传入多行代码的情况，最后一行为对象字面量时不能正确返回对象。如`let a = 1;\n{a: a}`不能返回对象。但一行代码的情况，用了人工添加括号的方式修复，可以正确返回，如：`{a: 1}`可正确返回对象。建议使用`eval`且需要执行多行代码时，自行为最后一行的表达式添加括号，如`let a = 1;\n({a: a})`。
- 为了实现的简洁，不再强行兼容es5及以下版本。
- 效率问题挺严重的。~~能用就行~~。

旧版本实现多行支持时用到反引号，详见GitHub链接的历史提交。这种实现会带来不少问题。新版本则改用如下方式实现：源代码在python层编码为utf-8，在**运行时解码**获得待执行的源代码。这种实现比旧版本好得多，但也有如下问题：

- `use_js_eval`选项开启后，某些表达式执行结果不正确。如：`ctx.eval('let a = 1\n{}',use_js_eval = True)`应返回空字典，却返回None。这是因为js使用`eval('{}')`返回undefined。我用人工添加括号的方式，修复了一行代码的情况。但由于多行代码的情况下，判定表达式的开头和结尾，并人工添加括号，是极其困难的工作，故我选择了放弃。
- 虽然本机使用没遇到，但仍可能存在未知的编码问题。

tips：

- 建议使用`eval`且需要执行多行代码时，自行为最后一行的表达式添加括号，如`let a = 1;\n({a: a})`。
- `main.py`是demo1，用到`crypto.js`；`test.py`是demo2，用到`utf8_code_demo.js`。

`myexecjs.py`

```python
import subprocess
import json

class ProcessExitedWithNonZeroStatus(Exception):
    def __init__(self, status, stdout, stderr):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr

    def __str__(self):
        return f'Process exited with status {self.status}\n{self.stdout}\n{self.stderr}'

class ProgramError(Exception):
    def __init__(self,v):
        self.v = v

    def __str__(self):
        return f'Program error: {self.v}'

node_wrap = lambda original,cur: """
(function (expression) {
  try {
    let result = expression();
    console.log('');
    if (typeof result == 'undefined' && result !== null) {
      console.log('["ok"]');
    } else {
      try {
        if (typeof result === 'bigint') result = '' + result;
        console.log(JSON.stringify(['ok', result]));
      } catch (err) {
        console.log('["err"]');
      }
    }
  } catch (err) {
    console.log(JSON.stringify(['err', '' + err]));
  }
})(function () {
%s
  ;return %s
})
""" % (original,cur)

def js_encodeURIComponent(b):
    ans = ''
    for c in b:
        ans += '%%%s' % (('00' if not c else ('0' if c < 16 else '')) + hex(c)[2:])
    return ans

class JsContext():
    def __init__(self,source = ''):
        self._source = source

    def get_inp(self,source,use_js_eval):
        if not source.strip():
            if use_js_eval: source = "eval('')"
            else: source = 'undefined'
        elif use_js_eval:
            # 给单行且使用eval的情况加上括号，如eval('({})')，多行情况弃疗
            if '\n' not in source:
                source = f'({source})'
            source_utf8 = js_encodeURIComponent(source.encode(encoding = 'utf-8'))
            # print('?????????',source_utf8)#
            source = 'eval(decodeURIComponent("%s"))' % (source_utf8)
        return node_wrap(self._source,source)

    def eval(self,source,use_js_eval = False):
        try:
            p = subprocess.Popen(
                ['node'],
                stdin = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                encoding = 'utf-8'
            )
            inp = self.get_inp(source,use_js_eval)
            res,stderrdata = p.communicate(input = inp)
            status = p.wait()
        finally:
            del p
        if status != 0:
            raise ProcessExitedWithNonZeroStatus(status = status, stdout = res, stderr = stderrdata)
        return self._extract_result(res)

    def _extract_result(self, output):
        output = output.replace("\r\n", "\n").replace("\r", "\n")
        output_last_line = output.split("\n")[-2]
        ret = json.loads(output_last_line)
        if len(ret) == 1:
            ret = [ret[0], None]
        status, value = ret
        if status == "ok":
            return value
        else:
            raise ProgramError(value)
```

`test.py`

```python
from myexecjs import JsContext,js_encodeURIComponent

def simple_multilines(ctx):
    print('simple_multilines::')
    # 简单的多行文本1
    res = ctx.eval('''
    let a = new A(`w${String.fromCharCode(97 + 18) + `w`}`,22);
    [a.name,a.age] = ['_' + a.name,a.age + 1];
    a
    ''',use_js_eval = True)
    print(res,type(res))
    print(res['name'],res['age'])
    assert type(res) == dict and res['name'] == '_wsw' and res['age'] == 23
    # 简单的多行文本2
    res = ctx.eval('''
    let v = add + '\\n'
    let w = add1 + '\\n' + A
    v + w
    ''',use_js_eval = True)
    print(res,type(res))

def combine_test():
    print('combine_test::')
    ctx = JsContext()
    res = ctx.eval('''
    const N = %s
    let C = Array.from({length: N},() => Array(N).fill(0))
    for(let i = 0;i < N;++i){
        C[i][0] = 1
        for(let j = 1;j <= i;++j){
            C[i][j] = C[i-1][j] + C[i-1][j-1]
        }
    }
    C
    ''' % (11),use_js_eval = True)
    for i in range(len(res)): print(res[i][:i+1])

def use_js_eval_test():
    print('use_js_eval_test::')
    ctx = JsContext()
    res = ctx.eval('1 + "\\n" + 2',use_js_eval = True)
    print(res,type(res))
    assert res == '1\n2'
    res = ctx.eval('1 + "\\n" + 2',use_js_eval = False)
    print(res,type(res))
    assert res == '1\n2'
    res = ctx.eval('1 + "\\t" + 2',use_js_eval = True)
    print(res,type(res))
    assert res == '1\t2'
    res = ctx.eval('1 + "\\t" + 2',use_js_eval = False)
    print(res,type(res))
    assert res == '1\t2'

def empty_test():
    print('empty_test::')
    ctx = JsContext()
    for fl in [False,True]:
        print(f'use_js_eval = {fl}::')
        res = ctx.eval('',use_js_eval = fl)
        print(res,type(res))
        assert res is None
        res = ctx.eval('{}',use_js_eval = fl)
        print(res,type(res))
        assert type(res) == dict
        res = ctx.eval("{a: %s + '4'}" % 123,use_js_eval = fl)
        print(res,type(res))
        assert type(res) == dict and res['a'] == '1234'
        res = ctx.eval('""',use_js_eval = fl)
        assert res == ''
        res = ctx.eval('+0',use_js_eval = fl)
        assert res == 0
        res = ctx.eval('-0',use_js_eval = fl)
        assert res == 0
        res = ctx.eval('null',use_js_eval = fl)
        assert res is None
        res = ctx.eval('undefined',use_js_eval = fl)
        assert res is None
        res = ctx.eval('Date()',use_js_eval = fl)
        print(res,type(res))

def utf8_code_demo():
    print('utf8_code_demo::')
    code = open('utf8_code_demo.js',encoding = 'utf-8').read()
    ctx = JsContext('let 变量 = 34')
    res = ctx.eval(code,use_js_eval = True)
    print(res)
    assert type(res) == float and abs(res - 200 - 2 / 3) < 1e-10

def test_js_encodeURIComponent():
    w = '''let v = add + '\\\\n'中文
    let w = add1 + '\\\\n' + A'''
    js_encodeURIComponent(w.encode(encoding = 'utf-8'))
    w = '未然形 打た 打とう 強かろう 勇敢だろう 连用形 打（う）ち 打って 強（つよ）く 勇敢（ゆうかん）に 终止形 打つ 強い 勇敢だ 连体形 打つ 強い 勇敢な 假定形 打てば 強ければ 勇敢なら(ば) 命令形 打て'
    js_encodeURIComponent(w.encode(encoding = 'utf-8'))

def main():
    test_js_encodeURIComponent()

    ctx = JsContext('''
    function add1(a,b){return `wsw${a+b+10}`}
    function add(...args){return args.reduce((s,v) => s + v,0)}
    class A{
        constructor(name,age){
            this.name = name
            this.age = age
        }
    }
    ''')
    for fl in [False,True]:
        print(f'use_js_eval = {fl}::')
        res = ctx.eval('add1(10,10)',use_js_eval = fl)
        print(res,type(res))
        assert res == 'wsw30'
        res = ctx.eval('BigInt(99 + 1) ** 9n + BigInt(100 * 2) ** 9n',use_js_eval = fl)
        print(res,type(res))
        assert res == '513000000000000000000'
        res = ctx.eval('add() + add(10,20,30,40)',use_js_eval = fl)
        print(res,type(res))
        assert res == 100
        # backquote
        print('backquote::')
        res = ctx.eval('`ha${`n` + String.fromCharCode(97 + 18)}`',use_js_eval = fl)
        print(res,type(res))
        assert res == 'hans'
        res = ctx.eval('new A(`w${String.fromCharCode(97 + 18)}w`,22)',use_js_eval = fl)
        print(res,type(res))
        print(res['name'],res['age'])
        assert res['name'] == 'wsw' and res['age'] == 22

    simple_multilines(ctx)
    # 不支持Promise
    # res = ctx.eval('new Promise((res) => {res(10)}).then((v) => v++)')

    combine_test()
    use_js_eval_test()
    empty_test()
    utf8_code_demo()

if __name__ == '__main__':
    main()
```

`main.py`

```python
from myexecjs import JsContext
import json
import subprocess

def main():
    goals = [
        'DG1uMMq1M7OeHhds71HlSMHOoI2tFpWCB4ApP00cVFqptmlFKjFu9RluHo2w3mUw',
        '3oimklW/W/ngYkFCAre5DPS4f/d4s9wsxAx+vxTeWY7Ab9AneJtN7AJr9elx7PLpSpxFUXsd0t0=',
        'sZkeRg+OqU4406ZO5EhpRUqsg9QS9dz4BANdNgmpsFVYJjNWn0k61E3lrj05r5EC',
        'evDiDnPBGwIxe3cjYPXB22oKj049pxLL3RfgIp5P9hT+tOtrsevTx29K9aaBj2Ds',
        'o6vkqk+dSV8jKFxlrQPB6S9GITUH4Fx8Kf4EI49OrTgM6c2ehRvua4osLn6iczH/IDcOr0DuFV9KnEVRex3S3Q==',
        'rR95BGefawHYyhz4VPfk6bkheavfgJcELQbGSxEWhB2Sna9EyCwZXhYyvHpf0X7NW3p0MRuPhYdE3KC6Bu3I5A==',
        'nTinqg2MTz6HPcn5po2mvK2hFB6CtN1VNYo3b7BUgrO7cZU7JmI4KETcoLoG7cjk',
        'SZrUq97bIKMT8A8+5poINKp4LvkMho6D22h7QAQdeaVt7lwUBMrzbKGsn4CWgWISSpxFUXsd0t0=',
        'jM2AMHWEGR7XPzcS9TXbFvWk3egklebrLpy4PGOJ2Dgp6gEMy+K7RC1pQBjov5z5',
        'ZbCyikQGss8IGCV14Utz07yC+ltW38oRRtagvPsNby+W5le06WT0SiAI79ae3rHi',
        '4QkDpTPjrgZdr6Mru2jvaxxik7n7Hs3GqA5xX/nVNMnpMvNi8r7WyLUe5gqPTte0+S7G053mkfc=',
        'LpC7uqNRalkxczZr61omV8D/Czy6GJR/0N56qHW8addmWsnr1LQ0VrtxlTsmYjgoRNygugbtyOQ=',
        'RsRBspJvKRto1876nMhHgh3Z6/9buixxfJZedby46Ydoywsc1boyIK4crMvnVmS2OS/I7URLXdw=',
        'OMHyOG8pDj5TH2yMM3zYJtdXdArhLFhp0ArpmcdGlYm87BsE44L1EOVOWatR++TjSpxFUXsd0t0=',
        '6C03P2Jzlff3i0amcVIMM/TdZLftH7b1xUuVHeeTaFlpMOkB0yHNHBbu7Z8EMDtMUVOJ3gkHn5I=',
        'TtulIkS1gMCQiGTImQtOZbPg/A766KPWnRe4RhZ6YxITyudvx3kTgiR0UGwcAEzr',
        'JWGteWDj2RBfHGC0jr8quHNUoJyrK2yIallL/iGyNwk=',
    ]
    crypto_js = 'crypto.js'
    ctx = JsContext(open(crypto_js,encoding = 'utf-8').read())

    hans = {
        'name': 'hans',
        'image': 'hans.png',
        'birthday': '1995-02-28',
        'height': '183cm',
        'weight': '58.8KG'
    }
    res = ctx.eval(f"getToken({json.dumps(hans,ensure_ascii = False)})")
    print(res,type(res),len(res))

    players = ctx.eval('players')
    players.append(hans)
    want1 = []
    # 效率问题挺严重的
    for p in players:
        want1.append(ctx.eval(f'getToken({json.dumps(p,ensure_ascii = False)})'))
    print(want1)

    want2 = ctx.eval('players.map(p => getToken(p))')
    print(want2)
    want2.append(res)
    assert want1 == goals and want2 == goals

if __name__ == '__main__':
    main()
```

### 参考链接

1. python的subprocess：https://www.cnblogs.com/lgj8/p/12132829.html
2. Python调用nodejs现在建议的方法（弃用pyexecjs、pyv8、js2py）：https://www.codenong.com/cs107102509/
3. https://cuiqingcai.com/2022114.html