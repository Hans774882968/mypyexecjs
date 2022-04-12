from myexecjs import JsContext

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

# use_js_eval = True时反斜杠用法不一致
def use_js_eval_test():
    print('use_js_eval_test::')
    ctx = JsContext()
    res = ctx.eval('1 + "\\\\n" + 2',use_js_eval = True)
    print(res,type(res))
    assert res == '1\n2'
    res = ctx.eval('1 + "\\n" + 2',use_js_eval = False)
    print(res,type(res))
    assert res == '1\n2'
    res = ctx.eval('1 + "\\\\t" + 2',use_js_eval = True)
    print(res,type(res))
    assert res == '1\t2'
    res = ctx.eval('1 + "\\t" + 2',use_js_eval = False)
    print(res,type(res))
    assert res == '1\t2'

def empty_test():
    print('empty_test::')
    ctx = JsContext()
    res = ctx.eval('',use_js_eval = True)
    print(res,type(res))
    assert res is None
    res = ctx.eval('',use_js_eval = False)
    print(res,type(res))
    assert res is None
    res = ctx.eval('{}')
    print(res,type(res))
    res = ctx.eval('""')
    assert res == ''
    res = ctx.eval('+0')
    assert res == 0
    res = ctx.eval('-0')
    assert res == 0
    res = ctx.eval('null')
    assert res is None
    res = ctx.eval('undefined')
    assert res is None
    res = ctx.eval('Date()')
    print(res,type(res))

def js_encodeURIComponent(b):
    ans = ''
    for c in b:
        ans += '%%%s' % (('00' if not c else ('0' if c < 16 else '')) + hex(c)[2:])
    return ans

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
    res = ctx.eval('add1(10,10)')
    print(res,type(res))
    assert res == 'wsw30'
    res = ctx.eval('BigInt(99 + 1) ** 9n + BigInt(100 * 2) ** 9n')
    print(res,type(res))
    assert res == '513000000000000000000'
    res = ctx.eval('add() + add(10,20,30,40)')
    print(res,type(res))
    assert res == 100
    # backquote
    print('backquote::')
    res = ctx.eval('`ha${`n` + String.fromCharCode(97 + 18)}`')
    print(res,type(res))
    assert res == 'hans'
    # `w${`s` + String.fromCharCode(97 + 18)}w`。开启use_js_eval后，即使是这种情况的反引号也无法处理，更别说更复杂的情况了
    res = ctx.eval('new A(`w${String.fromCharCode(97 + 18)}w`,22)')
    print(res,type(res))
    print(res['name'],res['age'])
    assert res['name'] == 'wsw' and res['age'] == 22
    # 简单的多行文本1
    res = ctx.eval('''
    let a = new A(`w${String.fromCharCode(97 + 18)}w`,22);
    [a.name,a.age] = ['_' + a.name,a.age + 1];
    a
    ''',use_js_eval = True)
    print(res,type(res))
    print(res['name'],res['age'])
    assert res['name'] == '_wsw' and res['age'] == 23
    # 简单的多行文本2
    res = ctx.eval('''
    let v = add + '\\\\n'
    let w = add1 + '\\\\n' + A
    v + w
    ''',use_js_eval = True)
    print(res,type(res))
    # 不支持Promise
    # res = ctx.eval('new Promise((res) => {res(10)}).then((v) => v++)')

    combine_test()
    use_js_eval_test()
    empty_test()

if __name__ == '__main__':
    main()