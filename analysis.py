import pandas
import matplotlib as mpl   # 字体模块
#from pylab import mpl
from matplotlib.font_manager import FontProperties
import matplotlib.pyplot as plt    # 绘图模块
from matplotlib.font_manager import *
import wordcloud
import jieba
from wordcloud import WordCloud
from scipy.misc import imread
import numpy as np


"""
#mpl.rcParams["font.sans-serif"] = ['SimHei']
myfont = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')

plt.rcParams["axes.labelsize"] = 16
plt.rcParams["xtick.labelsize"] = 15
plt.rcParams["ytick.labelsize"] = 10
plt.rcParams["legend.fontsize"] = 2   # 图例字体设置大小
plt.rcParams["figure.figsize"] = [15, 12]

def1 = pandas.read_csv('/home/cgh/dbs/bao.csv')
TBdata = pandas.DataFrame(list(zip(def1['nick'], def1['price']*def1['paid_people'])))

DD = TBdata.groupby([0]).sum()
DD[1].plot(kind='bar', rot=90)
#DD[1].plot(rot=90)  # 底下标旋转90度
plt.show()
"""

# 导入数据
#datatmsp = pandas.read_excel('/home/cgh/dbs/bao.xls')
datatmsp = pandas.read_csv('/home/cgh/dbs/bao.csv')

# 导入自定义分词表, 往jieba默认字典里add_word,即调用add_word方法
add_words = pandas.read_csv('/home/cgh/dbs/custom_words.csv')
for word in add_words.baobao_custom:
    jieba.add_word(word, freq=100)

# 取四列数据
data = datatmsp[['location', 'title', 'price', 'paid_people']]  # 为啥要两层？
print(data.head())   # 默认查看前5行

# 对location进行分割，取省份构成一列
data['province'] = data.location.apply(lambda x: x.split()[0])

# 因为淘宝商家地址除了直辖市就一个城市名外（北京天津上海重庆），
# 其他地址肯定是： 省份+城市，根据字符长度分割省份和城市
data['city'] = data.location.apply(lambda x: x.split()[0] if len(x) < 4 else x.split()[1])

data['sales'] = data['paid_people']

#print(data.dtypes)  # 查看各列数据类型
print(type(data.paid_people))
data['sales'] = data.sales.astype('int')  # 转换类型

list_col = ['province', 'city']
for i in list_col:
    data[i] = data[i].astype('category')    # ????

data.drop(['location', 'paid_people'], axis=1, inplace=True)

title = data.title.values.tolist()   # ??

# 用jieba的lcut函数对每个标题进行分词
title_s = []
for item in title:
    title_cut = jieba.lcut(item)   # 类似于split
    #print(title_cut)
    title_s.append(title_cut)
print(title_s)

# 导入停用词表
stopwords = pandas.read_csv('/home/cgh/dbs/stopwords.csv')
stopwords = stopwords.baobao_stopwords.values.tolist()   # 取values会以array形式返回
print(stopwords)

# 删除停用词
title_clean = []
for item in title_s:
    item_clean = []
    for word in item:
        if word not in stopwords:     # 判断每个词是否出现在停用词表中
            item_clean.append(word)
    title_clean.append(item_clean)
print("title_clean:", title_clean)

# 对经过以上分割与删除停用词后的每个item进行去重
title_clean_dist = []
for item in title_clean:
    item = set(item)
    title_clean_dist.append(list(item))

# 把所有的词放到一个列表
all_words_clean_dist = []
for item in title_clean_dist:
    for word in item:
        all_words_clean_dist.append(word)
print("all_words_clean_dist:", all_words_clean_dist)

# 把该列表转为数据框
df_allwords_clean_dist = pandas.DataFrame({"allwords": all_words_clean_dist})
print("df_allwords_clean_dist:\n", df_allwords_clean_dist)

#print(type(df_allwords_clean_dist.allwords.values), df_allwords_clean_dist.allwords.values.tolist())
print("test:\n", df_allwords_clean_dist.allwords)     # 不取列名的话得到的是一个对象，而且类似于可迭代的那种，但并不完全相同

word_count = df_allwords_clean_dist.allwords.value_counts().reset_index()   # 竟然能变成DataFrame
print("word_counts:\n", word_count)

# 给变成DataFrame的word_count的列名进行更改
word_count.columns = ['word', 'count']
print("new word_count:\n", word_count)

"""
开始制作词云
"""
plt.figure(figsize=(20, 10))
pic = imread("/home/cgh/图片/bao.jpeg")   # 自定义图片形状
w_c = WordCloud(font_path="/usr/share/fonts/夏日香气.ttf",
                background_color="white",
                mask=pic,
                max_font_size=100,
                margin=1)
wc = w_c.fit_words({x[0]:x[1] for x in word_count.head(150).values})
plt.imshow(wc, interpolation='bilinear')
plt.axis('off')
plt.show()

"""
分析出现频数靠前的各个关键词的各自销售总量
"""
# 先对所有关键词都进行操作，最后取销量最高的前几个关键词
w_s_sum = []
for w in word_count.word:
    List = []
    for index, item in enumerate(title_clean_dist):
        if w in item:
            List.append(data.sales[index])
    w_s_sum.append(sum(List))      # 把各自销售量结果放入列表

df_w_s_sum = pandas.DataFrame({'w_s_sum': w_s_sum})   # 以字典形式构造数据框

# 把word_count、df_w_s_sum合并成一个表
df_word_sum = pandas.concat([word_count, df_w_s_sum], axis=1, ignore_index=True)    # 参数：
print("df_word_sum:\n", df_word_sum)
# 对df_word_sum的列名改名
df_word_sum.columns = ['word', 'count', 'sales_sum']

# 取df_word_sum的word、sales_sum画图
df_word_sum.sort_values('sales_sum', inplace=True, ascending=True)  # 升序,则df会按上小下大来排列
print("df_word_sum after sort:\n ", df_word_sum)
df_n = df_word_sum.tail(30)    # 取数据框的后n行（由于前面进行了升序操作，最大的都在下面）
print("df_n:\n", df_n)
# matplotlib设置字体
#font = {'family': 'uming'}
#mpl.rc('font', **font)   # ??
"""
mpl.rcParams['font.sans-serif'] = ['STHeiti TC']
mpl.rcParams['axes.unicode_minus'] = False
"""
# 手动设置字体，用于下面调用
my_font = FontProperties(fname='/usr/share/fonts/夏日香气.ttf')

print("df_n.word.size:", df_n.word.size)
index = np.arange(df_n.word.size)
plt.figure(figsize=(6, 12))
# ????
plt.barh(index, df_n.sales_sum, color='purple', align='center', alpha=0.8)
plt.yticks(index, df_n.word, fontsize=11, fontproperties=my_font)  # 这里设置字体参数fontproperties
# ???
# 添加数据标签
for y, x in zip(index, df_n.sales_sum):
    plt.text(x, y, '%.0f' % x, ha='left', va='center', fontsize=11)
plt.show()
