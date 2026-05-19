# Security Checklist

Run before every public release PR:

```sh
git status --short
find . -path ./.git -prune -o -type f -size +1M -print
find . -path ./.git -prune -o -type f \( -iname '*.zip' -o -iname '*.rar' -o -iname '*.7z' -o -iname '*.tar' -o -iname '*.gz' -o -iname '*.pdf' -o -iname '*.csv' -o -iname '*.xlsx' -o -iname '*.xls' -o -iname '*.docx' -o -iname '*.pptx' -o -iname '*.html' -o -iname '*.log' -o -iname '*.db' -o -iname '*.sqlite' \) -print
rg -n -i --hidden --glob '!.git/**' '(api[_-]?key|secret|token|password|private[_-]?key|client[_-]?secret|authorization|bearer|cookie|session|credential|access[_-]?key|refresh[_-]?token|BEGIN (RSA|OPENSSH|PRIVATE) KEY)'
rg -n -i --hidden --glob '!.git/**' '(合同|报价|客户|学生|家长|订单|营收|成本|手机号|身份证|微信|邮箱|cookie|token|secret)'
```

Required interpretation:
- Any real secret or private data is a release blocker.
- Any generated/export/archive/media file is blocked until explicitly approved.
- Any platform resource identifier must be replaced with a placeholder or approved by the owner.

