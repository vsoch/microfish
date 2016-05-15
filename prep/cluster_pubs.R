library(pheatmap)
data = read.csv("microsoft_pubs.tsv",sep="\t",row.names=1)
data[is.null(data)] = 0
data[is.na(data)] = 0
pdf("microsoft_pubs.pdf",width=30,height=20)
pheatmap(data)
dev.off()