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