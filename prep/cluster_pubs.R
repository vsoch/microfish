library(pheatmap)
data = read.csv("microsoft_pubs.tsv",sep="\t",row.names=1)
pdf("microsoft_pubs.pdf",width=30,height=20)
pheatmap(data)
dev.off()

# Save clustering for plotting ourselves
hm = pheatmap(data)
