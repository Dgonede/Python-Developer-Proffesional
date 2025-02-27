"""A pure-Python Python bytecode interpreter."""
# Based on:
# pyvm2 by Paul Swartz (z3p), from http://www.twistedmatrix.com/users/z3p/

from __future__ import print_function, division
import dis
import inspect
import linecache
import logging
import operator
import sys
from collections import deque
import reprlib



from pyobj import Frame, Block, Method, Function, Generator

log = logging.getLogger(__name__)

if sys.version_info[0] < 3:
    byteint = ord
else:
    byteint = lambda b: b

# Create a repr that won't overflow.
repr_obj = reprlib.Repr()
repr_obj.maxother = 120
repper = repr_obj.repr


class VirtualMachineError(Exception):
    """For raising errors in the operation of the VM."""
    pass


class VirtualMachine:
    def __init__(self):
        # The call stack of frames.
        self.frames: list[Frame] = []
        # The current frame.
        self.frame: Frame | None = None
        self.return_value = None
        self.last_exception = None

    def top(self):
        """Return the value at the top of the stack, with no changes."""
        return self.frame.stack[-1]

    def pop(self, i=0):
        """Pop a value from the stack."""
        return self.frame.stack.pop(-1 - i)

    def push(self, *vals):
        """Push values onto the value stack."""
        self.frame.stack.extend(vals)

    def popn(self, n):
        """Pop a number of values from the value stack."""
        if n:
            ret = self.frame.stack[-n:]
            self.frame.stack[-n:] = []
            return ret
        else:
            return []

    def peek(self, n):
        """Get a value `n` entries down in the stack, without changing the stack."""
        return self.frame.stack[-n]

    def jump(self, jump):
        """Move the bytecode pointer to `jump`, so it will execute next."""
        self.frame.f_lasti = jump

    def push_block(self, type, handler=None, level=None):
        if level is None:
            level = len(self.frame.stack)
        self.frame.block_stack.append(Block(type, handler, level))

    def pop_block(self):
        return self.frame.block_stack.pop()

    def make_frame(self, code, callargs={}, f_globals=None, f_locals=None):
        log.info("make_frame: code=%r, callargs=%s" % (code, repper(callargs)))
        if f_globals is not None:
            if f_locals is None:
                f_locals = f_globals
        elif self.frames:
            f_globals = self.frame.f_globals
            f_locals = {}
        else:
            f_globals = f_locals = {
                '__builtins__': __builtins__,
                '__name__': '__main__',
                '__doc__': None,
                '__package__': None,
            }
        f_locals.update(callargs)
        frame = Frame(code, f_globals, f_locals, self.frame)
        return frame

    def push_frame(self, frame):
        self.frames.append(frame)
        self.frame = frame

    def pop_frame(self):
        self.frames.pop()
        if self.frames:
            self.frame = self.frames[-1]
        else:
            self.frame = None

    def print_frames(self):
        """Print the call stack, for debugging."""
        for f in self.frames:
            filename = f.f_code.co_filename
            lineno = f.line_number()
            print(f'  File "{filename}", line {lineno}, in {f.f_code.co_name}')
            linecache.checkcache(filename)
            line = linecache.getline(filename, lineno, f.f_globals)
            if line:
                print('    ' + line.strip())

    def resume_frame(self, frame):
        if frame.generator is None:
            log.error("Attempted to resume a frame without an active generator.")
            raise VirtualMachineError("No active generator to resume.")
    
        frame.f_back = self.frame
        val = self.run_frame(frame)
        frame.f_back = None
        return val

    def run_code(self, code, f_globals=None, f_locals=None):
        frame = self.make_frame(code, f_globals=f_globals, f_locals=f_locals)
        val = self.run_frame(frame)
        if self.frames:
            raise VirtualMachineError("Frames left over!")
        if self.frame and self.frame.stack:
            raise VirtualMachineError("Data left on stack! %r" % self.frame.stack)

        return val

    def unwind_block(self, block):
        if block.type == 'except-handler':
            offset = 3
        else:
            offset = 0

        while len(self.frame.stack) > block.level + offset:
            self.pop()

        if block.type == 'except-handler':
            tb, value, exctype = self.popn(3)
            self.last_exception = exctype, value, tb

    def parse_byte_and_args(self):
        """Parse 1 - 3 bytes of bytecode into an instruction and optionally arguments."""
        f = self.frame
        opoffset = f.f_lasti
        byteCode = f.f_code.co_code[opoffset]
        f.f_lasti += 1
        byteName = dis.opname[byteCode]
        arg = None
        arguments = []
        if byteCode >= dis.HAVE_ARGUMENT:
            arg = f.f_code.co_code[f.f_lasti:f.f_lasti + 2]
            f.f_lasti += 2
            intArg = arg[0] + (arg[1] << 8)
            if byteCode in dis.hasconst:
                arg = f.f_code.co_consts[intArg]
            elif byteCode in dis.hasfree:
                if intArg < len(f.f_code.co_cellvars):
                    arg = f.f_code.co_cellvars[intArg]
                else:
                    var_idx = intArg - len(f.f_code.co_cellvars)
                    arg = f.f_code.co_freevars[var_idx]
            elif byteCode in dis.hasname:
                arg = f.f_code.co_names[intArg]
            elif byteCode in dis.hasjrel:
                arg = f.f_lasti + intArg
            elif byteCode in dis.hasjabs:
                arg = intArg
            elif byteCode in dis.haslocal:
                arg = f.f_code.co_varnames[intArg]
            else:
                arg = intArg
            arguments = [arg]

        return byteName, arguments, opoffset

    def log(self, byteName, arguments, opoffset):
        """Log arguments, block stack, and data stack for each opcode."""
        op = f"{opoffset}: {byteName}"
        if arguments:
            op += f" {repr(arguments[0])}"
        indent = "    " * (len(self.frames) - 1)
        stack_rep = repper(self.frame.stack)
        block_stack_rep = repper(self.frame.block_stack)

        log.info(f"  {indent}data: {stack_rep}")
        log.info(f"  {indent}blks: {block_stack_rep}")
        log.info(f"{indent}{op}")

    def dispatch(self, byteName, arguments):
        try:
            if byteName.startswith('UNARY_'):
                self.unaryOperator(byteName[6:])
            elif byteName.startswith('BINARY_'):
                self.binaryOperator(byteName[7:])
            elif byteName.startswith('INPLACE_'):
                self.inplaceOperator(byteName[8:])
            elif 'SLICE+' in byteName:
                self.sliceOperator(byteName)
            elif byteName == 'RESUME':
            # Проверка наличия активного генератора
                if self.frame.generator is None:
                    log.error("Attempted to resume a generator, but none is active.")
                    raise VirtualMachineError("No generator to resume")
            # Обработка байт-кода RESUME
                why = self.handle_resume(*arguments)
            else:
                bytecode_fn = getattr(self, f'byte_{byteName}', None)
                if not bytecode_fn:
                    raise VirtualMachineError(f"unknown bytecode type: {byteName}")
                why = bytecode_fn(*arguments)

        except Exception:
            self.last_exception = sys.exc_info()[:2] + (None,)
            log.exception("Caught exception during execution")
            why = 'exception'

        return why
    

    def handle_resume(self, *args):
        if self.frame.generator is None:
            log.error("Attempted to resume a generator, but none is active.")
            raise VirtualMachineError("No generator to resume")

        log.info("Resuming generator with args: %s", args)
        try:
            return self.frame.generator.send(*args)
        except StopIteration as e:
            self.return_value = e.value
            self.pop_frame()  # Удаляем фрейм генератора
            return 'return'
    

    def manage_block_stack(self, why):
        """Manage a frame's block stack."""
        assert why != 'yield'

        block = self.frame.block_stack[-1]
        if block.type == 'loop' and why == 'continue':
            self.jump(self.return_value)
            why = None
            return why

        self.pop_block()
        self.unwind_block(block)

        if block.type == 'loop' and why == 'break':
            why = None
            self.jump(block.handler)
            return why

        if block.type in ['finally', 'setup-except'] and why == 'exception':
            if why == 'exception':
                exctype, value, tb = self.last_exception
                self.push(tb, value, exctype)
            else:
                if why in ('return', 'continue'):
                    self.push(self.return_value)
                self.push(why)

            why = None
            self.jump(block.handler)
            return why

        return why

    def run_frame(self, frame):
        """Run a frame until it returns (somehow)."""
        self.push_frame(frame)
        while True:
            byteName, arguments, opoffset = self.parse_byte_and_args()
            if log.isEnabledFor(logging.INFO):
                self.log(byteName, arguments, opoffset)

            why = self.dispatch(byteName, arguments)

            if why == 'reraise':
                why = 'exception'

            if why != 'yield':
                while why and frame.block_stack:
                    why = self.manage_block_stack(why)

            if why:
                break

        self.pop_frame()

        if why == 'exception':
            raise self.last_exception[0](self.last_exception[1]).with_traceback(self.last_exception[2])

        return self.return_value

    ## Stack manipulation

    def byte_LOAD_CONST(self, const):
        self.push(const)

    def byte_POP_TOP(self):
        self.pop()

    def byte_DUP_TOP(self):
        self.push(self.top())

    def byte_DUP_TOPX(self, count):
        items = self.popn(count)
        self.push(*items)

    def byte_DUP_TOP_TWO(self):
        # Py3 only
        a, b = self.popn(2)
        self.push(a, b, a, b)

    def byte_ROT_TWO(self):
        a, b = self.popn(2)
        self.push(b, a)

    def byte_ROT_THREE(self):
        a, b, c = self.popn(3)
        self.push(c, a, b)

    def byte_ROT_FOUR(self):
        a, b, c, d = self.popn(4)
        self.push(d, a, b, c)

    ## Names

    def byte_LOAD_NAME(self, name):
        frame = self.frame
        if name in frame.f_locals:
            val = frame.f_locals[name]
        elif name in frame.f_globals:
            val = frame.f_globals[name]
        elif name in frame.f_builtins:
            val = frame.f_builtins[name]
        else:
            raise NameError(f"name '{name}' is not defined")
        self.push(val)

    def byte_STORE_NAME(self, name):
        self.frame.f_locals[name] = self.pop()

    def byte_DELETE_NAME(self, name):
        del self.frame.f_locals[name]

    def byte_LOAD_FAST(self, name):
        if name in self.frame.f_locals:
            val = self.frame.f_locals[name]
        else:
            raise UnboundLocalError(f"local variable '{name}' referenced before assignment")
        self.push(val)

    def byte_STORE_FAST(self, name):
        self.frame.f_locals[name] = self.pop()

    def byte_DELETE_FAST(self, name):
        del self.frame.f_locals[name]

    def byte_LOAD_GLOBAL(self, name):
        f = self.frame
        if name in f.f_globals:
            val = f.f_globals[name]
        elif name in f.f_builtins:
            val = f.f_builtins[name]
        else:
            raise NameError(f"global name '{name}' is not defined")
        self.push(val)

    def byte_STORE_GLOBAL(self, name):
        f = self.frame
        f.f_globals[name] = self.pop()

    def byte_LOAD_DEREF(self, name):
        self.push(self.frame.cells[name].get())

    def byte_STORE_DEREF(self, name):
        self.frame.cells[name].set(self.pop())

    def byte_LOAD_LOCALS(self):
        self.push(self.frame.f_locals)

    ## Operators

    UNARY_OPERATORS = {
    'POSITIVE': operator.pos,
    'NEGATIVE': operator.neg,
    'NOT': operator.not_,
    'CONVERT': repr,
    'INVERT': operator.invert,
}

def unaryOperator(self, op):
    x = self.pop()
    self.push(self.UNARY_OPERATORS[op](x))

BINARY_OPERATORS = {
    'POWER': pow,
    'MULTIPLY': operator.mul,
    'DIVIDE': operator.truediv,
    'FLOOR_DIVIDE': operator.floordiv,
    'MODULO': operator.mod,
    'ADD': operator.add,
    'SUBTRACT': operator.sub,
    'SUBSCR': operator.getitem,
    'LSHIFT': operator.lshift,
    'RSHIFT': operator.rshift,
    'AND': operator.and_,
    'XOR': operator.xor,
    'OR': operator.or_,
}

def binaryOperator(self, op):
    x, y = self.popn(2)
    self.push(self.BINARY_OPERATORS[op](x, y))

def inplaceOperator(self, op):
    x, y = self.popn(2)
    if op == 'POWER':
        x **= y
    elif op == 'MULTIPLY':
        x *= y
    elif op == 'DIVIDE':
        x /= y  
    elif op == 'FLOOR_DIVIDE':
        x //= y
    elif op == 'MODULO':
        x %= y
    elif op == 'ADD':
        x += y
    elif op == 'SUBTRACT':
        x -= y
    elif op == 'LSHIFT':
        x <<= y
    elif op == 'RSHIFT':
        x >>= y
    elif op == 'AND':
        x &= y
    elif op == 'XOR':
        x ^= y
    elif op == 'OR':
        x |= y
    else:
        raise VirtualMachineError(f"Unknown in-place operator: {op!r}")
    self.push(x)

def sliceOperator(self, op):
    start = 0
    end = None
    op, count = op[:-2], int(op[-1])
    if count == 1:
        start = self.pop()
    elif count == 2:
        end = self.pop()
    elif count == 3:
        end = self.pop()
        start = self.pop()
    l = self.pop()
    if end is None:
        end = len(l)
    if op.startswith('STORE_'):
        l[start:end] = self.pop()
    elif op.startswith('DELETE_'):
        del l[start:end]
    else:
        self.push(l[start:end])

COMPARE_OPERATORS = [
    operator.lt,
    operator.le,
    operator.eq,
    operator.ne,
    operator.gt,
    operator.ge,
    lambda x, y: x in y,
    lambda x, y: x not in y,
    lambda x, y: x is y,
    lambda x, y: x is not y,
    lambda x, y: issubclass(x, Exception) and issubclass(x, y),
]

def byte_COMPARE_OP(self, opnum):
    x, y = self.popn(2)
    self.push(self.COMPARE_OPERATORS[opnum](x, y))

## Attributes and indexing

def byte_LOAD_ATTR(self, attr):
    obj = self.pop()
    val = getattr(obj, attr)
    self.push(val)

def byte_STORE_ATTR(self, name):
    val, obj = self.popn(2)
    setattr(obj, name, val)

def byte_DELETE_ATTR(self, name):
    obj = self.pop()
    delattr(obj, name)

def byte_STORE_SUBSCR(self):
    val, obj, subscr = self.popn(3)
    obj[subscr] = val

def byte_DELETE_SUBSCR(self):
    obj, subscr = self.popn(2)
    del obj[subscr]

## Building

def byte_BUILD_TUPLE(self, count):
    elts = self.popn(count)
    self.push(tuple(elts))

def byte_BUILD_LIST(self, count):
    elts = self.popn(count)
    self.push(elts)

def byte_BUILD_SET(self, count):
    elts = self.popn(count)
    self.push(set(elts))

def byte_BUILD_MAP(self, size):
    self.push({})

def byte_STORE_MAP(self):
    the_map, val, key = self.popn(3)
    the_map[key] = val
    self.push(the_map)

def byte_UNPACK_SEQUENCE(self, count):
    seq = self.pop()
    for x in reversed(seq):
        self.push(x)

def byte_BUILD_SLICE(self, count):
    if count == 2:
        x, y = self.popn(2)
        self.push(slice(x, y))
    elif count == 3:
        x, y, z = self.popn(3)
        self.push(slice(x, y, z))
    else:
        raise VirtualMachineError(f"Strange BUILD_SLICE count: {count!r}")

def byte_LIST_APPEND(self, count):
    val = self.pop()
    the_list = self.peek(count)
    the_list.append(val)

def byte_SET_ADD(self, count):
    val = self.pop()
    the_set = self.peek(count)
    the_set.add(val)

def byte_MAP_ADD(self, count):
    val, key = self.popn(2)
    the_map = self.peek(count)
    the_map[key] = val

## Printing

def byte_PRINT_ITEM(self):
    item = self.pop()
    self.print_item(item)

def byte_PRINT_ITEM_TO(self):
    to = self.pop()
    item = self.pop()
    self.print_item(item, to)

def byte_PRINT_NEWLINE(self):
    self.print_newline()

def byte_PRINT_NEWLINE_TO(self):
    to = self.pop()
    self.print_newline(to)

def print_item(self, item, to=None):
    if to is None:
        to = sys.stdout
    if hasattr(to, 'softspace') and to.softspace:
        print(" ", end="", file=to)
        to.softspace = 0
    print(item, end="", file=to)
    if isinstance(item, str):
        if (not item) or (not item[-1].isspace()) or (item[-1] == " "):
            to.softspace = 1
    else:
        to.softspace = 1

def print_newline(self, to=None):
    if to is None:
        to = sys.stdout
    print("", file=to)
    if hasattr(to, 'softspace'):
        to.softspace = 0

## Jumps

def byte_JUMP_FORWARD(self, jump):
    self.jump(jump)

def byte_JUMP_ABSOLUTE(self, jump):
    self.jump(jump)

def byte_POP_JUMP_IF_TRUE(self, jump):
    val = self.pop()
    if val:
        self.jump(jump)

def byte_POP_JUMP_IF_FALSE(self, jump):
    val = self.pop()
    if not val:
        self.jump(jump)

def byte_JUMP_IF_TRUE_OR_POP(self, jump):
    val = self.top()
    if val:
        self.jump(jump)
    else:
        self.pop()

def byte_JUMP_IF_FALSE_OR_POP(self, jump):
    val = self.top()
    if not val:
        self.jump(jump)
    else:
        self.pop()

    ## Blocks

def byte_SETUP_LOOP(self, dest):
    self.push_block('loop', dest)

def byte_GET_ITER(self):
    self.push(iter(self.pop()))

def byte_FOR_ITER(self, jump):
    iterobj = self.top()
    try:
        v = next(iterobj)
        self.push(v)
    except StopIteration:
        self.pop()
        self.jump(jump)

def byte_BREAK_LOOP(self):
    return 'break'

def byte_CONTINUE_LOOP(self, dest):
    self.return_value = dest
    return 'continue'

def byte_SETUP_EXCEPT(self, dest):
    self.push_block('setup-except', dest)

def byte_SETUP_FINALLY(self, dest):
    self.push_block('finally', dest)

def byte_END_FINALLY(self):
    v = self.pop()
    if isinstance(v, str):
        why = v
        if why in ('return', 'continue'):
            self.return_value = self.pop()
        if why == 'silenced':  # PY3
            block = self.pop_block()
            assert block.type == 'except-handler'
            self.unwind_block(block)
            why = None
    elif v is None:
        why = None
    elif isinstance(v, BaseException):
        exctype = v
        val = self.pop()
        tb = self.pop()
        self.last_exception = (exctype, val, tb)
        why = 'reraise'
    else:
        raise VirtualMachineError("Confused END_FINALLY")
    return why

def byte_POP_BLOCK(self):
    self.pop_block()

def byte_RAISE_VARARGS(self, argc):
    cause = exc = None
    if argc == 2:
        cause = self.pop()
        exc = self.pop()
    elif argc == 1:
        exc = self.pop()
    return self.do_raise(exc, cause)

def do_raise(self, exc, cause):
    if exc is None:  # повторный вызов
        exc_type, val, tb = self.last_exception
        if exc_type is None:
            return 'exception'  # ошибка
        else:
            return 'reraise'

    elif isinstance(exc, type):
        exc_type = exc
        val = exc()  
    elif isinstance(exc, BaseException):
        exc_type = type(exc)
        val = exc
    else:
        return 'exception'  # ошибка
    if cause:
        if isinstance(cause, type):
            cause = cause()
        elif not isinstance(cause, BaseException):
            return 'exception'  # ошибка

        val.__cause__ = cause

    self.last_exception = exc_type, val, val.__traceback__
    return 'exception'

def byte_POP_EXCEPT(self):
    block = self.pop_block()
    if block.type != 'except-handler':
        raise Exception("popped block is not an except handler")
    self.unwind_block(block)

def byte_SETUP_WITH(self, dest):
    ctxmgr = self.pop()
    self.push(ctxmgr.__exit__)
    ctxmgr_obj = ctxmgr.__enter__()
    self.push_block('finally', dest)
    self.push(ctxmgr_obj)

def byte_WITH_CLEANUP(self):
    v = w = None
    u = self.top()
    if u is None:
        exit_func = self.pop(1)
    elif isinstance(u, str):
        if u in ('return', 'continue'):
            exit_func = self.pop(2)
        else:
            exit_func = self.pop(1)
        u = None
    elif isinstance(u, BaseException):
        w, v, u = self.popn(3)
        exit_func = self.pop()
        self.push(w, v, u)
        block = self.pop_block()
        assert block.type == 'except-handler'
        self.push_block(block.type, block.handler, block.level - 1)
    else:
        raise VirtualMachineError("Confused WITH_CLEANUP")

    exit_ret = exit_func(u, v, w)
    err = (u is not None) and bool(exit_ret)
    if err:
        
        self.push('silenced')


    ## Functions

def byte_MAKE_FUNCTION(self, argc):
    name = self.pop()
    code = self.pop()
    defaults = self.popn(argc)
    globs = self.frame.f_globals
    fn = Function(name, code, globs, defaults, None, self)
    self.push(fn)

def byte_LOAD_CLOSURE(self, name):
    self.push(self.frame.cells[name])

def byte_MAKE_CLOSURE(self, argc):
    name = self.pop()
    closure, code = self.popn(2)
    defaults = self.popn(argc)
    globs = self.frame.f_globals
    fn = Function(name, code, globs, defaults, closure, self)
    self.push(fn)

def byte_CALL_FUNCTION(self, arg):
    return self.call_function(arg, [], {})

def byte_CALL_FUNCTION_VAR(self, arg):
    args = self.pop()
    return self.call_function(arg, args, {})

def byte_CALL_FUNCTION_KW(self, arg):
    kwargs = self.pop()
    return self.call_function(arg, [], kwargs)

def byte_CALL_FUNCTION_VAR_KW(self, arg):
    args, kwargs = self.popn(2)
    return self.call_function(arg, args, kwargs)

def call_function(self, arg, args, kwargs):
    lenKw, lenPos = divmod(arg, 256)
    namedargs = {}
    for i in range(lenKw):
        key, val = self.popn(2)
        namedargs[key] = val
    namedargs.update(kwargs)
    posargs = self.popn(lenPos)
    posargs.extend(args)

    func = self.pop()
    frame = self.frame
    if hasattr(func, '__self__'):
        if func.__self__:
            posargs.insert(0, func.__self__)
        if not isinstance(posargs[0], func.__class__):
            raise TypeError(
                f'unbound method {func.__name__}() must be called with {func.__class__.__name__} instance '
                f'as first argument (got {type(posargs[0]).__name__} instance instead)'
            )
        func = func.__func__
    retval = func(*posargs, **namedargs)
    self.push(retval)

def byte_RETURN_VALUE(self):
    self.return_value = self.pop()
    if self.frame.generator:
        self.frame.generator.finished = True
    return "return"

def byte_YIELD_VALUE(self):
    self.return_value = self.pop()
    return "yield"

def byte_YIELD_FROM(self):
    u = self.pop()  # Получаем значение, которое будет отправлено
    x = self.top()  # Получаем текущий генератор

    log.info(f"Yielding from generator: {x}, sending value: {u}")

    try:
        if not isinstance(x, Generator):
            raise TypeError("Expected a generator")
        
        if u is None:
            retval = next(x)  # Получаем следующее значение из генератора
        else:
            retval = x.send(u)  # Отправляем значение в генератор
        
        self.return_value = retval
    except StopIteration as e:
        self.pop()  # Удаляем завершенный генератор
        self.push(e.value)  # Возвращаем значение завершения
        log.info(f"Generator finished with value: {e.value}")
    else:
        self.jump(self.frame.f_lasti - 1)  # Возвращаемся к предыдущему байт-коду
        return "yield"

## Importing

def byte_IMPORT_NAME(self, name):
    level, fromlist = self.popn(2)
    frame = self.frame
    self.push(
        __import__(name, frame.f_globals, frame.f_locals, fromlist, level)
    )

def byte_IMPORT_STAR(self):
    mod = self.pop()
    for attr in dir(mod):
        if attr[0] != '_':
            self.frame.f_locals[attr] = getattr(mod, attr)

def byte_IMPORT_FROM(self, name):
    mod = self.top()
    self.push(getattr(mod, name))

## And the rest...

def byte_EXEC_STMT(self):
    stmt, globs, locs = self.popn(3)
    exec(stmt, globs, locs) 

def byte_LOAD_BUILD_CLASS(self):
    
    self.push(__build_class__)

def byte_STORE_LOCALS(self):
    self.frame.f_locals = self.pop()