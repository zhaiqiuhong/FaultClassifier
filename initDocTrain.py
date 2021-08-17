from typing import List

import gensim
from gensim.corpora import Dictionary
import os
import jieba

# 未打乱的model的映射    60.5%
# model_label = [5, 4, 1, 3, 2, 6, 0]   # 1、6一个都不会中
# true_label = [1, 2, 3, 4, 5, 6, 7]

# 自己修改数据
model_label = [0, 2, 3, 5, 6, 1, 4]
true_label = [1, 2, 3, 4, 5, 6, 7]

def load_stopword():
    f_stop = open('Data/cn_stopwords.txt', encoding='utf-8')
    stopwords = [line.strip() for line in f_stop]
    f_stop.close()
    return stopwords

def tokenize(text):
    stop_words = load_stopword()
    return [token for token in jieba.cut(text) if token not in stop_words]

def doSingleTest():
    single_topic = ""  # 分类结果
    while(1):
        test_str = input("请输入故障状态：")
        if test_str == "exit":
            break
        tokenized_test_str = tokenize(test_str)
        corpus = dictionary.doc2bow(tokenized_test_str)
        result = lda_model.get_document_topics(corpus)
        label_prob = []  # 用于保存7个类对应的概率
        for label_tuple in result:
            label_prob.append(label_tuple[1])
        for label_tuple in result:
            if label_tuple[1] == max(label_prob):
                single_topic = label_tuple[0]
                break  # 暂时不考虑两个概率相同的情况
        print("故障分类：" + str(mapLabel(single_topic)))
        print("该分类的前5个关键字是：" + lda_model.print_topic(single_topic, 5))

def mapLabel(label):
    label_map_list = map(lambda x, y : (x, y), model_label, true_label)
    for label_map in label_map_list:
        if label_map[0] == label:
            return label_map[1]

def doListTest(sub_dic):
    # test_list = ["正极对地开路电压值为0伏", "组串线虚接，熔断器及座发热、烧黑", "通讯数据静止无变化，防雷器失效"
    #     , "过载脱扣", "监控模块没有电压", "通讯端子松动", "流经模块内电流值异常高"]
    test_path = "Data/" + sub_dic + "/" + "test.txt"
    test_list = []
    test_label_list = []

    with open(test_path, "r") as testFile:
        for line in testFile:
            test_label = line.split("\t",1)[0]
            test_str = line.split("\t",1)[1]
            test_str = test_str.replace(" ", "").replace("\n", "")
            if test_str.__len__() == 0:
                continue
            test_label_list.append(test_label)
            test_list.append(test_str)
    processed_test_list = [tokenize(test) for test in test_list]
    corpus_test = [dictionary.doc2bow(test) for test in processed_test_list]
    # topic_result_test = lda_model.get_document_topics(corpus_test)
    topic_result_test = []
    for i in range(test_list.__len__()):
        result = lda_model.get_document_topics(corpus_test[i])
        topic_result_test.append(result)

    # 整理每个test_doc的lda分类结果
    max_topic = []
    for i in range(test_list.__len__()):
        label_prob = []  # 用于保存类对应的概率
        for label_tuple in topic_result_test[i]:
            label_prob.append(label_tuple[1])
        for label_tuple in topic_result_test[i]:
            if label_tuple[1] == max(label_prob):
                max_topic.append(label_tuple[0])
                break  # 暂时不考虑两个概率相同的情况

    # 统计映射
    map_list = []   # 6个元素，每个元素中有7个tuple，（model_label, num）
    label_num_list = [30, 30, 26, 33, 30, 28, 61]
    count_model_label_list = []
    # label_id = 1   # original label
    count = 0  #用于表示已统计过的label数
    for label_num in label_num_list:
        count_model_label_list = [0, 0, 0, 0, 0, 0, 0]  # 大小为7，存放对应7种得到的label数
        for j in range(label_num):  # 统计某一类
            count_model_label_list[max_topic[count + j]] \
                = count_model_label_list[max_topic[count + j]] + 1
        map_list.append(count_model_label_list)
        count = count + label_num


    correct = 0
    # 与正确label进行比对
    for i in range(test_list.__len__()):
        label_model = max_topic[i]
        label_origin = mapLabel(label_model)
        if str(label_origin) == test_label_list[i]:
            correct = correct + 1

    print("模型精确度为：" + str(round((correct/test_list.__len__())*100, 2)) + "%")


    # for i in range(test_topic_num):
    #     # print("这条" + label_list_test[i] + "类故障的分类结果为：")
    #     print("故障的分类结果为：")
    #     for result in topic_result_test[i]:
    #         print(result)
    #     # max_topic = max(topic_result_test[i])
    #
    #     label_prob = []  # 用于保存7个类对应的概率
    #     for label_tuple in topic_result_test[i]:
    #         label_prob.append(label_tuple[1])
    #     for label_tuple in topic_result_test[i]:
    #         if label_tuple[1] == max(label_prob):
    #             max_topic.append(label_tuple[0])
    #             break  # 暂时不考虑两个概率相同的情况
    #     print("最有可能属于第" + str(max_topic[i]) + "\n")
    #     print("该分类的前5个关键字是：" + lda_model.print_topic(max_topic[i], 5))
    #     print("\n")

def getLdaModel():
    model_name = "./model.lda"
    if os.path.exists(model_name):
        lda_model = gensim.models.LdaModel.load(model_name)
        print("loaded from old")
    else:
        # preprocess()
        lda_model = gensim.models.LdaModel(corpus=bag_of_words_corpus, num_topics=7, id2word=dictionary)
        lda_model.save(model_name)
        print("loaded from new")
    return lda_model

if __name__ == '__main__':
    sub_dic = "second"

    file = open('Data/' + sub_dic + '/' + 'train.txt', encoding='utf-8')

    processed_docs = [tokenize(doc.split("\t", 1)[1].replace(" ", "").replace("\n", "")) for doc in file]  # 分词

    dictionary = Dictionary(processed_docs)   #构建词典

    bag_of_words_corpus = [dictionary.doc2bow(pdoc) for pdoc in processed_docs]

    # 以上内容放在main()中是因为dictionary变量后续也要用到
    # train part
    lda_model = getLdaModel()

    for i in range(7):
        print("分类"+ str(i) +"的前5个关键字是：" + lda_model.print_topic(i, 5)+"\n")

    # test part
    test_mode = input("请输入测试模式：")
    if test_mode == "list":   # 输入测试集，获得模型精确度
        doListTest(sub_dic)
    elif test_mode == "single":  # 终端输入输出演示用
        doSingleTest()
    else:
        quit()



