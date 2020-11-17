const {NotImplementedError} = require("./common.js");


class ParsingError extends Error {
    toString() {
        return `ParsingError: ${this.message}`;
    }
}


const _parse_fspec = (function _parse_fspec(spec) {
    /** @type FSpec */
    let ret_val = {
        grouping_option: null,
        precision: null,
        sign: null,
        width: null,
        fill: null,
        align: null,
        type: null,
        alternate: false
    };

    // const regex = /(.[<>^=]|)([-+ ]?)(#?)(0?)(\d*)([_,]?)(\.\d+)([bcdeEfFgGnosxX%]?)/;
    let state = 0;
    // 0 = fill
    for (let i = 0; i < spec.length; i++) {
        console.log({spec, ret_val, state, i, speci: spec[i]});
        if (state === 0) {
            if ("<>^=".includes(spec[i + 1])) {
                // next chat is align, current must be fill
                ret_val.fill = spec[i];
                state += 1;
                continue;  // eat char
            } else {
                state = 2; // skip over fill since there is none
            }
        }
        if (state === 1) {
            ret_val.align = spec[i];
            state += 1;
            continue;  // eat char
        }
        if (state === 2) {
            state += 1;
            if ("-+ ".includes(spec[i])) {
                ret_val.sign = spec[i];
                continue;  // eat char
            }
        }
        if (state === 3) {
            state += 1;
            if (spec[i] === "#") {
                ret_val.alternate = true;
                continue;  // eat char
            }
        }
        if (state === 4) {
            state += 1;
            if (spec[i] === "0") {
                ret_val.align = ret_val.align ?? "=";
                ret_val.fill = ret_val.fill ?? "0";
                continue;  // eat char
            }
        }
        if (state === 5) {
            state += 1;
            if ("0123456789".includes(spec[i])) {
                ret_val.width *= 10;
                ret_val.width += Number(spec[i]);
                state -= 1;  // return here on next character if possible
                continue;  // eat character
            }
        }
        if (state === 6) {
            state += 1;
            if ("_,".includes(spec[i])) {
                ret_val.grouping_option = spec[i];
                continue;  // eat character
            }
        }
        if (state === 7) {
            if (spec[i] === ".") {
                state = 8;
                continue;  // eat character
            } else {
                state = 9;
            }
        }
        if (state === 8) {
            state += 1;
            if ("0123456789".includes(spec[i])) {
                ret_val.precision *= 10;
                ret_val.precision += Number(spec[i]);
                state -= 1;  // return here on next character if possible
                continue;  // eat character
            }
        }
        if (state === 9) {
            state += 1;
            if ("bcdeEfFgGnosxX%".includes(spec[i])) {
                ret_val.type = spec[i];
                continue;  // eat character
            }
        }

        if (state === 10) {
            throw new ParsingError("oops, something happened");
        }
    }
    return ret_val;
});

const real_py__range = (function* real_py__range(start, end, step) {
    for (let i = 0; i < end; i += step) {
        yield i;
    }
});

module.exports = {
    format: (function py__format(value, fspec) {
        if (typeof value.__format__ !== 'undefined') {
            return value.__format__(fspec);
        } else {
            /** @type FSpec */
            const spec = _parse_fspec(fspec);
            throw NotImplementedError("__format__ is not implemented YET.");
        }
    }),
    py__range: (function py__range(...args) {
        if (args.length === 1) {
            return real_py__range(0, args[0], 1);
        } else if (args.length === 2) {
            return real_py__range(args[0], args[1], 1);
        } else if (args.length === 3) {
            return real_py__range(args[0], args[1], args[2]);
        } else {
            throw SyntaxError(`Given bad amount of arguments for function py__range (Python range): ${args.length}, expected 1, 2 or 3`);
        }
    }),
    py__iter: (function py__iter(target) {
        console.debug("Warn: ignored argument for py__iter");
        return target;
    })
};
/**
 * @typedef FSpec {{grouping_option: string, precision: number, sign: string, width: number, fill: string, align: string, type: string}}
 */
