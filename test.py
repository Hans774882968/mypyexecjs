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