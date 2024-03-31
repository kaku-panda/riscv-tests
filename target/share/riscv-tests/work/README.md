# エミュレータ側
```
spike -d --isa=RV32IMAFDC ../isa/rv32ui-p-add
```
* reg 0 レジスタ番号

```
spike -l --isa=RV32IMAFDC ../isa/rv32ui-p-add > output.log 2>&1
```
* PC の確認には上記コマンドが最適
