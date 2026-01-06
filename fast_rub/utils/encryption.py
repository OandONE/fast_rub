class Encryption:
    @staticmethod
    def _clip(n):
        return max(32, min(126, n))
    @staticmethod
    def _compute_enc(code, pos, pat):
        if pat == 0:
            return code + pos * 10, "A"
        elif pat == 1:
            return code * 3 + pos, "B"
        elif pat == 2:
            return (code << 2) + pos * 5, "C"
        else:
            return 1000 - code + pos * 7, "D"
    @staticmethod
    def _compute_dec(val, pos, mark):
        if mark == "A":
            return val - pos * 10
        elif mark == "B":
            return (val - pos) // 3
        elif mark == "C":
            return (val - pos * 5) >> 2
        else:
            return 1000 - val + pos * 7
    @staticmethod
    def _scramble_hex(h):
        return h[::-1]
    @staticmethod
    def _unscramble_hex(h):
        return h[::-1]
    @staticmethod
    def en(text):
        out = []
        for i, ch in enumerate(text):
            pos = i + 1
            pat = i % 4
            code = ord(ch)
            val, mark = Encryption._compute_enc(code, pos, pat)
            hex_val = f"{val:06X}"
            scr = Encryption._scramble_hex(hex_val)
            block = f"{mark}{pos:03d}{scr}"
            out.append(block)
        return "{" + ",".join(out) + "}"
    @staticmethod
    def de(encoded):
        encoded = encoded.strip("{}")
        blocks = encoded.split(",")
        out = []
        for block in blocks:
            mark = block[0]
            pos = int(block[1:4])
            scr_hex = block[4:]
            hex_val = Encryption._unscramble_hex(scr_hex)
            val = int(hex_val, 16)
            code = Encryption._compute_dec(val, pos, mark)
            out.append(chr(Encryption._clip(code)))
        return "".join(out)
