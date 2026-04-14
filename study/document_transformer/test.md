5-1 第1章 大模型RAG应用开发基础及入门
5-1-1 本章介绍
大模型出现幻觉及缓解方案

- 了解大语言模型出现幻觉的原因,涵盖数据层面、模型层面的相关解释,以及幻觉的评估基准。
- 了解常见的大语言模型幻觉缓解方案,涵盖了调整模型参数、外挂知识、多智能体互动、加入诚实样本等。
- 学习什么是RAG以及基础架构,并尝试在ChatGPT上手动模拟RAG的运行流程加深理解。
  AI应用开发利器——向量数据库
- 学习了解什么是向量数据库,以及使用场景,为什么需要向量数据库,与传统数据库之间的差异。
- 了解什么是词向量,在LLM应用开发中的用途,掌握几种常见的词向量相似度计算方法,了解向量数据库的索引和搜索,底层如何加速相似度搜索过程。
- 掌握各类向量数据库的配置部署与使用,涵盖商用类型、云端数据库、开源本地部署等。
  文本嵌入模型与RAG应用初步开发
- 了解什么是文本嵌入模型，掌握利用文本嵌入模型提取非结构化数据的特征。
- 了解几种不同类型的文本嵌入模型使用技巧,不同维度的词向量使用的场景与优缺点。
- 利用LangChain基于向量数据库构建第一个RAG应用,实现一个基于知识库问答的聊天机器人。
  5-1-2 大语言模型出现幻觉的原因及缓解方案
  幻觉的定义及出现的原因
  幻觉的定义
  大语言模型在处理自然语言时,有时会出现幻觉,表现为回答不准确或前后不一致的问题,这些幻觉可以分为两类:

1. 事实性幻觉:指模型生成的内容与可验证的现实事实不一致。比如提问"第一个在月球上行走的人是谁?",模型回复"Charles Lindbergh在1951年月球先驱任务中第一个登上月球",而实际上,第一个登上月球的人是Neil Armstrong。而事实性幻觉又分为事实不一致(与现实世界信息相矛盾)和事实捏造(压根没有,无法根据现实信息验证)。
2. 忠实性幻觉:指模型生成的内容与用户的指令或上下文不一致。比如让模型总结今年10月的新闻,结果模型却在说2006年10月的事。忠实性幻觉也可以细分,分为指令不一致(输出偏离用户指令)、上下文不一致(输出与上下文信息不符)、逻辑不一致(推理步骤以及与最终答案之间不一致)三类,
   产生幻觉的原因
   那么致使大模型产生幻觉的原因都有哪些?其实可以划分成三大来源:教据源、调练过程和推理
   数据源导致的幻觉
   首先病从口入,大模型的粮食数据,是致使它产生幻觉的一大原因。这里面就包括 数据缺陷和数据中捕获的事实知识的利用率低,
   具体来说,数据缺陷分为错误信息和偏见(重复偏见、社会偏见),此外大模型也存在知识边界,所以存在领域知识缺陷和过时的事实知识。即便大模型吃掉了大量的数据,也会在利用时出现问题。
   除此之外,大模型可能会过度依赖训练数据中的一些模式,如位置接近性、共现统计数据和相关文档计数,从而导致幻觉,比如:如果训练数据中频繁出现"加拿大"和"多伦多",那么大模型可能会错误地也将多伦多识别为加拿大的首都。
   训练过程导致的幻觉
   在模型的预训练阶段(大模型学习通用表示并获取世界知识)、对齐阶段(微调大模型使其更好地与人类偏好一致)两个阶段产生的问题也会导致幻觉的发生,
   预训练阶段可能会存在:

- 架构缺陷:基于前一个token预测下一个token,这种单向建模阻碍了模型捕获复杂的上下文关系的能力;自注意力模块存在缺陷,随着token长度增加,不同位置的注意力被稀释,
- 暴露偏差:训练策略也有缺陷,模型推理时依赖于自己生成的token进行后续预测,模型生成的错误token会在整个后续token中产生级联错误。
  对齐阶段可能会存在:
- 能力错位:大模型内在能力与标注数据中描述的功能之间可能存在错位。当对齐数据需求超出这些预定义的能力边界时,大模型会被训练来生成超出其自身知识边界的内容,从而放大幻觉的风险
- 信念错位:基于RLHF等的微调,使大模型的输出更符合人类偏好,但有时模型会倾向于迎合人类偏好,从而牺牲信息真实性。
  推理导致的幻觉
  大模型产生幻觉的第三个关键因素是推理,存在两个问题:

1. 固有的抽样随机性:在生成内容时根据概率随机生成。
2. 不完美的解码表示:上下文关注不足(过度关注相邻文本而忽视了源上下文)和softmax瓶颈(输出概率分布的表达能力受限)。
   大模型幻觉的评估
   目前对于大模型幻觉的评估,对于 事实性幻觉和 忠实性幻觉有不同的评估方法。
   其中 事实性幻觉,有检索外部事实和不确定性估计两种方法。
   校索外部事实是将模型生成的内容与可靠的知识来源进行比较,例如同一个问题利用大语言模型生成内容,同时和外部检索到真实的信息进行对比校验。
   而不确定性估计的幻觉检测方法有两类:基于内部状态的方法和基于行为的方法。
3. 基于内部状态的方法主要依赖于大模型的内部状态。例如,通过考虑关键概念的最小标记概率来确定模型的不确定性
4. 基于行为的方法主要依赖观察大模型的行为,不需要访问具内部状态,例如,通过采样多个响应并评估事实陈述的一致性来检测幻觉。

而检测 忠实性幻觉也有5种主流方法:

1. 基于事实的度量:测量生成内容和源内容之间事实的重叠程度来评估忠实性。
2. 分类器度量:使用训练过的分类器来区分模型生成的忠实内容和幻觉内容。
3. 问答度量:使用问答系统来验证源内容和生成内容之间的信息一致性
4. 不确定度估计:测量模型对其生成输出的置信度来评估忠实性。
5. 提示度量:让大模型作为评估者,通过特定的提示策略来评估生成内容的忠实性
   大语言模型幻觉的缓解方案
   幻觉和创造/创新/涌现其实只有一线之隔,大模型如果没有幻觉,那就永远无法产生新内容,所以,从涌现/创新的角度来说,大模型的幻觉永远不会被解决,在某些场合下只可能被缓解。
   大语言模型幻觉的缓解方案也有数据、预训练、对齐、推理相关的方案,与LLM应用开发相关的主要在数据方面的处理。
   缓解数据相关幻觉(重点)
   减少错误信息和偏见,最直观的方法是收集高质量的事实数据,并进行数据清理以消除偏见。对于大语言模型知识边界的问题,有两种流行方法。一种是知识编辑,直接编辑模型参数弥合知识差距。另一种通过检索增强生成(RAG)利用非参数知识源。
   检索增强生成具体分为三种类型:一次性检索、选代检索和事后检索,
   [图片]

- 一次性检索是将从单次检索中获得的外部知识直接预置到大模型的提示中;
- 迭代检索允许在整个生成过程中不断收集知识;
- 事后检索是基于检索的修订来完善大模型输出。

后续使用一次性检索,
缓解预训练相关幻觉

1. 改进模型架构:使用双向自回归模型和注意力锐化技术,增强模型对上下文的理解
2. 优化训练目标:通过引入事实性增强的训练方法和上下文预川练,提升模型的事实关联和逻辑一致性
3. 减少曝光偏差:采用新的监督信号和解码策略,减少训练与准理过程中的幻觉。
   缓解对齐相关幻觉
4. 减少能力错位:通过改进人类偏好判断,确保模型生成内容在其知识范围内。
5. 减少信念错位:聚合人类偏好和调整模型内部激活,减少模型迎合行为,避免生成与模型自身认知相悖的内容。
   缓解推理相关幻觉
6. 增强事实性解码:动态调整解码策略,利用模型内部结构引导事实性回答。
7. 增强忠实度解码:通过上下文和逻辑一致性策略,确保模型输出与用户指令或上下文保持一致,
   5-1-3检索增强生成RAG基础架构与手动模拟
   检索增强生成RAG基础
   什么是RAG?
   检索增强生成(RAG)是指对大型语言模型输出进行优化,使其能够在生成响应之前引用训练数据来源之外的权威知识库。大型语言模型(LLM)用海量数据进行训练,使用数十亿个参数为回答问题、翻译语言和完成句子等任务生成原始输出,在LLM本就强大的功能基础上,RAG将其扩展为能访问特定领域或组织的内部知识库,所有都无需重新训练模型,是一种经济高效地改进LLM输出的方法,让它在各种情境下都能保持相关性、准确性和实用性。
   简单理解:RAG就是从外部先检索对应的知识内容,和用户的提问一起构成Prompt,再让LLM生成内容。
   如果为前面开发的聊天机器人架构添加上RAG模块,更新后的运行流程如下:
   [图片]
   RAG的重要性及优点
   我们可以将LLM看成是一个过于热情的员工,而且这个员工拒绝了解任何时事,但是他总是会很自信地回答每一个问题,更不幸的是这个员工回答态度非常好,内容非常流畅,一般情况下还很难看出是真是假!所以单纯利用LLM进行开发,存在非常大的缺陷:
8. LLM的训练数据是静态的,这意味着LLM掌握的知识是有时间限制的,对于新知识不了解。
9. 当用户需要待定或者即时的数据时,LLM往往提供通用或者过时的数据
10. LLM回答的内容可能是从非权威来源创建响应,
11. 由于术语混淆,不同的培训来源使用相同的术语来谈论不不同的事情,因此会产生不确定的响应,
    对比其他解决LLM幻觉的方案,RAG带来的好处也非常明显:
12. 经济高效:预训练和微洞模型的成本很高,相比之下,RAG是一种经济高效将新输入引入LLM的方案,
13. 信息即时:使用RAG可以为LLM提供最新的研究、统计数据或新闻,确保数据的即时性。
14. 增强用户信任度:RAG允许LLM通过来源归属来量现准确的信息,输出可以包括对来源的引文或引用,如果需要进一步说明或更详细的信息,用户也可以自己查找源文档。这可以增加对您的生成式人工智能解决方案的信任和信心。4.开发人员拥有更多控制权:借助RAG,开发人员可以更高效地测试和改进他们的聊天应用程序。他们可以控制和更改LLM的信息来源,以适应不断变化的需求或跨职能使用。开发人员还可以将敏感信息的检索限制在不同的授权级别内,并确保LLM生成适当的的响应。此外,如果LLM针对特定问题引用了错误的信息来源,他们还可以进行故障排除并进行修复。组织可以更自信地为更广泛的应用程序实施生成式人工智能技术。
    ChatGPT手动模拟RAG运行流程
    人类与大语言模型的主要交接方式就是通过Prompt,所以通过Playground/ChatGPT手动模拟RAG的过程其实也非常简单,使用用户的提问query进行搜索,得到搜索相关的内容,将搜索的内容与有预设的Prompt模板、用户的query拼接成最终提示词,传递给大语言模型即可模拟最基础的RAG运行流程,
    实际在代码中,无论多么复杂的RAG、无论如何进行RAG优化,本质上都是执行外部检索,然后将外部检索的内容和用户原始提问合并成最终Prompt,再向大语言模型发起提问,最终得到对应的内容。
    5-1-4 AI应用开发新宠——向量数据库的介绍与用途
    "猫"与向量的关系与衍生
    如果我们使用一个水平轴来表示 体型大小 这个特征,这些不同品种的猫将落在不同的坐标点上,这样就可以通过体型的大小区分出一些品种,如下:
    [图片]
    然而,如果仅仅靠体型一个特征,依旧会有很多品种的猫特征相近,比如缅因猫、奶牛毛和折耳猫就非常接近,所以以我们继续添加多一个特征,比如毛发的长短,继续建立一个毛发的垂直轴,这样子就可以区分出更多品种,
    随着特征增加，向量轴也以此增加
    如果这个时候还想引入更多的特征进行区分,比如:眼睛火小、尾巴长短、毛发颜色、声音大小、耳朵形状等等,虽然在坐标图没法展示出来,但是我们却可以很轻松地将这些特征使用数值的方式展示出来,例如下方
    [图片]
    当记录的特征足够大,维度足够大时,区分的程度也会越高,当看到一只猫,只需要将它转换成对应的多维坐标数据/向量,就可以很轻松地找到这只猫的分类归属,而且不仅仅是猫,几乎所有的事物都可以使用这一套方式进行表达。
    所以一个字、一个词、一句话、一篇文本、甚至一张图片都可以用这样一个多维坐标数据,亦或者说向量记录对应的特征,而将文本转换为记录特征的向量就可以被称为词向量。
    向量数据库概念与用途
    向量数据库就是一种专门用于存储和处理向量数据的数据库系统,传统的关系型数据库通常不擅长处理向量数据,因为它们需要将数据映射为结构化的表格形式,而 向量数据的维度较高、结构复杂,导致传统数据库存储和查询效率低下,所以向量教据库应运而生,
    由于高维的向量我们在三维空间没法绘图,这里我们以二维向量的形式扩展到多维,来一起看下向星的神通广大之处!
    例如下图,在二维坐标上,概念上更接近的点,在图表上也更聚集,而那些概念上不同的点则一般距离比较远。
    [图片]
    如果将两个点之间作差,得到一条新的向量,甚至我们可以使用这条结果向量来表示两个点之间的关联(越短表示关联越大),相比传统的数据库,向量数据库针对向量距离/相似度计算进行了特定的的优化,如下:
    [图片]
    所以最常见的应用就是人脸识别,将不同的人脸归一化(固定大小)后生成对应的向量,然后将千干万万张人脸的向量进行存储。
    进行人脸识别时,只需要将这张人脸按照统一的标准归一化并转换成向量,接下来在向量数据库中搜索与这个向量最接近的向量,就可以巧妙实现人脸识别。

这也是向量数据库的最常使用场景:人脸识别、图像搜索、音频识别、智能推荐系统等。
而在RAG中,我们将对应的知识文档按照特定的规则拆分成合适的大小,再转换成向量存储到向量数据库中,当人类提问时,人类提问query转换成向量并进行搜索,找到在特征上更接近的文本块,这些文本块就可以看成和query具有强关联或者说有因果关系。
这样就可以将这些文本块作为这次提问的额外补充知识,让LLM基于补充知识+提问生成对应的内容,从而实现知识库问答。
5-1-5 传统数据库与向量数据库的使用差异
两种数据库的差异
搜索方式差异
传统数据库,比如关系型数据库,擅长处理结构化数据,如存储在表格中的的文本和数字等,它们通过预定义的查询语言(如SQL)来进行精确匹配或条件搜索,这种方式在处理银行交易、客户信息等数据时效果显著,但在处理复杂的模式识别问题时就显得力不从心。
例如,通过SELECT + WHERE 可以精准查询到id为 e0d13c78-870b-46df-b2f5-693ae9d5d727 的用户
SELECT \* FROM account WHERE id='e0d13c78-870b-46Sdf-b2f5-693ae9d5d727
但是想通过SQL来查询和我喜欢打篮球游泳与编程这句话语义相近的内容,就无能力为了,
相比之下,向量数据库不是通过匹配确切的数值,而是通过 种称为相似性搜索的方法来工作。它们可以快速找到与查询向量最相似的数据点(目前绝大部分向量数据库都支持在相似性搜索的基础上上添加筛选条件),即使这些数据点在数值上并不完全相同
例如,在一个向量数据库中,即使没有完全相同的照片,我们仍然可以找到风格相似的图片。通过这种方式,向量数据库打破了传统数据库的局限,为处理和分析大规模、复杂的数据提供了更灵活和强大的解决方案
数据处理与存储差异
传统数据库采用基于行的存储方式,传统数据库将数据存为行记录,每一行包含多个字段,并且每个字段都有固定的列,传统数据库通常使用索引来提高查询性能,例如下方就是一个典型的传统充数据库表格:
[图片]
这种方式在处理结构化数据时非常高效,但在处理非结构化或半结构化数据时效率低下,
向量数据库将数据以列形式存储,即每个列都有一个独立的存储空间,这使得向量数据库可以更加灵活地处理复杂的数据结构。向量数据库还可以进行列压缩(稀疏矩阵),以减少存储空间和提高数据的访问速度
并且在向量数据库中,将数据表示为高维向量,其中每个向量对应于数据点,这些向量之间的距离表示它们之间的相似性。这种方式使得非结构化或半结构化数据的存储和检索变得更加高效。
以电影数据库为例,我们可以将每部电影表示为一个特征向量。假设我们使用四个特征来描述每部电影:动作、冒险、爱情、科幻。每个特征都可以在0到1的范围内进行标准化,表示该电影在该特征上的强度。
例如,电影"阿凡达"的向量表示可以是[0.9,0.8.0.2,0.9],其中数字分别表示动作、冒险、爱情、科幻的特征强度。其他电影也可以用类似的方式表示。这些向量可以存储在向量数据库中,如下所示:
[图片]
现在,如果我们想要直找与电影"阿凡达"相似的电影,我们可以计算向量之间的距离,找到最接近的向量,从而实现相似性匹配而无需复杂的SQL查询,这就像使用地图找到两个地点之间的最短路径一样简单,
优缺点横向对比
尽管向量数据库在处理高维数据和实现快速检索方面有着显著优势,但它并不是一种"一刀切"的解决方案。在某些应用场景中,其他类型的数据库可能更合适,而且向量数据库与传统关系数据库协同发展、相互补充,
[图片]
相似性搜索算法
余弦相似度与欧式距离
在向量数据库中,支持通过多种方式来计算两个向量的相似以度,例如:余弦相似度、欧式距离、曼哈顿距离、闵可夫斯基距离、汉明距离、Jaccard相似度等多种。其中最常见的就是余弦相似度和欧式距离
例如下图,左侧就是欧式距离,右侧就是余弦相似度。
[图片]
[图片]
相似性搜索加速计算
在向量数据库中,数据按列进行存储,通常会将多个向量组织成一个M×N的矩阵,其中M是向量的维度(特征数),N是向量的数量(数据库中的条目数),这个矩阵可以是稠密或者稀疏的,取决于于向量的稀疏性和具体的存储优化策略。
这样计算相似性搜索时,本质上就变成了向量与M×N矩阵的每一行进行相似度计算,这里可以用到大量成熟的加速算法:

1. 矩阵分解方法:

- SVD(奇异值分解):可以通过奇异值分解将原始矩阵转换为更低秩的短阵表示,从而减少计算量。
- GPCA(主成分分析):类似地,可以通过主成分分析将高维矩阵映射到低维空间,减少计算复杂度。

2. 索引结构和近似算法:

- LSH(局部敏感哈希):LSH可以在近似相似度匹配中加速计算,特别适用于高维稀疏向量的情况。
- ANN(近似最近邻)算法:ANN算法如KD-Tree、Ball-Tree等可以人用来加速对最近邻搜索的计算,虽然主要用于向量空间,但也可以部分应用于相似度计算中。

3. GPU加速:使用图形处理单元(GPU)进行并行计算可以显著提高相似度计算的速度,尤其是对于大规模数据和高维度向量,
4. 分布式计算:由于行与行之间独立,所以可以很便捷地支持分布式计算每行与向量的相似度,从而加速整体计算过程。
   向量数据库底层除了在算法层面上针对相似性搜索做了大量优化,在存储结构、索引机制等方面均做了大量的优化,这才使得向量数据库在处理高维数据和实现快速相似性搜索上展示出巨大的优势。
   5-1-6Embedding文本嵌入模型介绍与使用
   什么是Embedding?
   要想使用向量数据库的相似性搜索,存储的数据必须是向量,那么如何将高维度的文字、图片、视频等非结构化数据转换成向量呢?这个时候就需要使用到Embedding嵌入模型了,例如下方就是Embeddir1g嵌入模型的运行流程:
   [图片]
   Embedding 模型是一种在机器学习和自然语言处理中广泛应用的的技术,它旨在将高纬度的数据(如文字、图片、视频)映射到低纬度的空间。Embedding向量是一个N维的实值向量,它将输入的数据表示成一个连续的数值空间中的点。这种嵌入可以是一个词、一个类别特征(如商品、电影、物品等)或时间序列特征等。
   而且通过学习,Embedding 向量可以更准确地表示对应特征的内在含义,使几何距离相近的向量对应的物体有相近的含义,甚至对向量进行加减乘除算法都有意义!
   一句话理解Embedding:一种模型生成方法,可以将非结构化的数据,例如文本/图片/视频等数据映射成有意义的向量数据。
   目前生成embedding方法的模型有以下4类:
5. Word2Veg(词嵌入模型):这个模型通过学习将单词转化为连续的向量表示,以便计算机更好地理解和处理文本。Word2Vec模型基于两种主要算法CBOW和skip-gram,
6. Glove:一种用于自然语言处理的词嵌入模型,它与其他常见的词嵌入模型(如Word2Vec和FastText)类似,可以将单词转化为连续的向量表示。Glove模型的原理是通过观察单词在语料库中的共现关系,学习得到单词之间的语义关系。具体来说,Glove模型将共现概率矩阵表示为两个词向量之间的点积和偏差的关系,然后通过迭代优化来训练得到最佳的词向量表示。
   Glove模型的优点是它能够在大规模语料库上进行有损压缩,得到较小维度的词向量,同时保持了单词之间的语义关系,这些词向量可以被用于多种自然语言处理任务,如词义相似度计算、情感分析、文本分类等。
7. FastText:一种基于词袋模型的词嵌入技术,与其他常见的词司嵌入模型(如Word2Vec和GloVe)不同之处在于,FastText考虑了单词的子词信息。其核心思想是将单词视为字符的n-grams的集合,在训练过程中,模型会同时学习单词级别和n-gram级别的表示。这样可以捕捉到单词内部的细粒度信息,从而更好地处理各种形态和变体的单词。
8. 大模型Embeddings(重点):和大模型相关的嵌入模型,如OpenAl官方发布的第二代模型:text-embedding-ada-002。它最长的输入是8191个tokens,输出的维度是1536。
   Embedding带来的价值
9. 降维:在许多实际问题中,原始数据的维度往往非常高。例如,在自然语言处理中,如果使用Token词表编码来表示词汇,其维度等于词汇表的大小,可能达到数十万甚至更高,通过Embedding,我们可以将这些高维数据映射到一个低维空间,大大减少了没型的复杂度。
10. 捕捉语义信息:Embedding不仅仅是降维,更重要的是,它能够捕捉到数据的语义信息。例如,在词嵌入中,语义上相近的词在向量空间中也会相近。这意味着Embedding可以保留并利用原始数据的一些重要信息
11. 适应性:与一些传统的特征提取方法相比,Embedding是通过数据驱动的方式学习的,这意味着它能够自动适应数据的特性,而无需人工设计特征。
12. 泛化能力:在实际问题中,我们经常需要处理一些在训练数据中没有有出现过的数据,由于Embedding能够捕捉到数据的一些内在规律,因此对于这些未见过的数据,Fmbedding仍然能够给出合理里的表示,
13. 可解释性:尽管Embedding是高维的,但我们可以通过一些可视化工具(如l-SNE)来观察和理解Embedding的结构,这对于理解模型的行为,以及发现数据的一些潜在规律是非常有用的。
    Embedding的运算法则
    通过对上文的理解,我们继续看看训练好的词向量实例(也被称为词嵌入),并探索他们的一些有趣属性(一个当成是玩笑的例子,主要用于帮助大家更好去理解Embedding,该例子在其他Embedding极型下不不一定能复现),
    这是一个"king"词的嵌入(使用Glove方法生成的向量):
    [图片]
    这是一个50维的向量,通过数字我们很难观察其规律,但是我们可以将这个向量的每一个元素进行可视化颜色编码,由于范围是[-2,2),越靠近-2则设置成蓝色,越靠近2则设置成红色,那么这一串向最就可以表示成这样:
    [图片]
    我们忽略数字仅查看颜色,并且将"King"与其他单词进行比较(King国王、Man男人、Woman女人):
    [图片]
    从色块分布图中,可以很容易的看出King、Man、Woman这三组向量的结构其实非常接近,色块颜色非常集中,这是否能意味着国王、男人、女人这三个词之间是具有强关联甚至是子集的因果关系
    扩张这个图，加入更多的向量
    [图片]
    在这张分布图中也可以轻松看出一些信息:
14. 这几个单词的词向量在中间都有一条直的红色列,代表它们在这个维度上是相似的,但是从数值来看我们看不出这个维度是什么。
15. woman和girl在很多地方都是相似的,man和boy也一样。
16. girl和boy也有一些彼此相似的地方,但这些和woman/girl不同,这些差异是否可以总结出"年龄"这个维度?
17. 上面的单词中,除了water其他的都和人相关,并且向量的到数第三个元素是一个蓝色的色块,来到water这里却消失了。
18. king和queen非常接近,但是存在一些比较明显的差异,这部分差是异是否能体现出"性别"这个维度?
    除了单个词的向量能展示出一些有意思的信息,对向量进行加多或乘除也能得到一些有意思的结果,在NLP界有一个非常名的公式:
    Queen = King - Man + Woman
    女王=国王-男人+女人
    对这几个向量进行运算后,同样可视化出来,结果如下:
    [图片]
    你会发现king-man-woman和queen的向量特征分布非常接近,也是GloVe集合中40w个字嵌入中最接近它的词。
    这一个示例虽然不一定是一个正确的思路,但是从这个示例中仍然然可以看到将对应的词转换成Embedding向量后,嵌入模型能够用捉到数据的语义信息,并且语义上相近的词在向量空间中也会相近,这也为语义搜索提供了一个可能。
    5-1-7OpenAlEmbedding接口使用实践测试
    OpenAl Embedding嵌入模型
    OpenAl服务提供商提供了线上的Embeddings服务,涵盖了3种模型,信息对比如下:
    [图片]
    OpenAl的Embeddings嵌入模型虽然是市面上效果最好的嵌入模型,虽然价格非常低廉,不过由于没有本地版本,而且接口响应速度相对较慢,在需要对大量文档进行嵌入时,效率非常低,所以国内使用得并不多(国内一般会使用对应的本地或者本地服务提供商的嵌入模型)。
    OpenAl Embeddings官网文档:https://platform.openai.com/docs/guides/embeddings
    Embedding组件使用
    在LangChain中,Embeddings类是一个专为与文本嵌入模型交互而设计的类,这个类为许多嵌入模型提供商(如OpenAl、Cohere、Hugging Face等)提供一个标准的接口。
    LangChain中Embeddings类提供了两种方法:
19. embed_documents:用于嵌入文档列表,传入一个文档列表,寻到这个文档列表对应的向量列表。
20. embed_query:用于嵌入单个查询,传入一个字符串,得到这个字符串对应的向量。
    并且Embeddings类并不是一个Runnable组件,所以并不能直接接入到Runnable序列链中,需要额外的RunnableLambda函数进行转换,核心基类代码也非常简单:
    import dotenv
    from langchain_openai import OpenAIEmbeddings
    import numpy

dotenv.load_dotenv()

# 1.创建文本嵌入模型

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 2.嵌入文本

query_vector = embeddings.embed_query("我叫Robin，我喜欢打篮球")

# print(query_vector)

# print(len(query_vector)) # 1536

# 3.嵌入文档列表/字符串列表

documents_vector = embeddings.embed_documents(
["我叫Robin，我喜欢打篮球", "这个喜欢打篮球的人叫Robin", "求知若渴，虚心若愚"]
)

print(len(documents_vector)) # 3

# 计算相似度

def cos_similarity(vec1: list, vec2: list) -> float:
"""计算传入两个向量的余弦相似度""" # 1. 计算两个向量的点积
dot_product = numpy.dot(vec1, vec2)

    # 2. 计算两个向量的长度
    vec1_length = numpy.linalg.norm(vec1)
    vec2_length = numpy.linalg.norm(vec2)

    # 3.计算余弦相似度
    return dot_product / (vec1_length * vec2_length)

# 计算余弦相似度

print(
"向量1和向量2的相似度：", cos_similarity(documents_vector[0], documents_vector[1])
) # 向量1和向量2的相似度： 0.8646846062415526

print(
"向量1和向量3的相似度：", cos_similarity(documents_vector[0], documents_vector[2])
) # 向量1和向量3的相似度： 0.0868669237226309

越靠近1越相似
5-1-8 CacheBackEmbedding组件的使用与注意事项
CacheBackEmbedding使用与场景
通过嵌入模型计算传递数据的向量需要昂贵的算力,对于重复的内容,Embeddings计算的结果肯定是一致的,如果数据重复仍然二次计算,会导致效率非常低,而且增加无用功。
所以在LangChain中提供了一个叫CacheBackEmbedding的包装类,一般通过类方法from_bytes_store进行实例化,它接受以下参数:

1. underlying_embedder:用于嵌入的嵌入模型。
2. document_embedding_cache:用于缓存文档嵌入的任何存储库(ByteStore).
3. batch_size:可选参数,默认为None,在存储更新之间要嵌入的文档数量。
4. namespace:可选参数,默认为空,用于文档缓存的命名空间。此命名空间用于避免与其他缓存发生冲突。例如,将其设置为所使用的嵌入模型的名称。
5. query_embedding_cache:可选默认为None或者不缓存,用于缓存查询/文本嵌入的ByteStore,或者是为True以使用与document_embedding_cache相同的存储。
   注意事项:CacheBackEmbedding默认不缓存embed_query生成的向量,如果要缓存,需要设置query_embedding_cache的值,另外请尽可能设置namespace,以避免使用不同嵌入模型嵌入的相同文本发生冲突。

借用上节课的例子：
import dotenv
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_classic.embeddings import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore

import numpy

dotenv.load_dotenv()

# 2. 缓存目录

cache_dir = Path(**file**).resolve().parent / "cache"

# 3. 文件缓存 store

store = LocalFileStore(str(cache_dir))

# 1.创建文本嵌入模型

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
embeddings_with_cache = CacheBackedEmbeddings.from_bytes_store(
embeddings,
store,
namespace=embeddings.model,
query_embedding_cache=True,
)

# 2.嵌入文本

query_vector = embeddings_with_cache.embed_query("我叫Robin，我喜欢打篮球")

# print(query_vector)

# print(len(query_vector)) # 1536

# 3.嵌入文档列表/字符串列表

documents_vector = embeddings_with_cache.embed_documents(
["我叫Robin，我喜欢打篮球", "这个喜欢打篮球的人叫Robin", "求知若渴，虚心若愚"]
)

print(len(documents_vector)) # 3

# 计算相似度

def cos_similarity(vec1: list, vec2: list) -> float:
"""计算传入两个向量的余弦相似度""" # 1. 计算两个向量的点积
dot_product = numpy.dot(vec1, vec2)

    # 2. 计算两个向量的长度
    vec1_length = numpy.linalg.norm(vec1)
    vec2_length = numpy.linalg.norm(vec2)

    # 3.计算余弦相似度
    return dot_product / (vec1_length * vec2_length)

# 计算余弦相似度

print(
"向量1和向量2的相似度：", cos_similarity(documents_vector[0], documents_vector[1])
) # 向量1和向量2的相似度： 0.8646846062415526

print(
"向量1和向量3的相似度：", cos_similarity(documents_vector[0], documents_vector[2])
) # 向量1和向量3的相似度： 0.0868669237226309

第一次运行会慢，然后将结果写入缓存
再次运行就会快，会读缓存
CacheBackEmbedding运行流程
CacheBackEmbedding底层的运行流程非常简单,本质上就是封装了一个持久化存储的数据存储仓库,在每次进行数据嵌入前,会从前数据存储仓库中检索对对应的向量,然后逐个匹配对应的数据是否相等,找到缓存中没有的文本,然后将这些文本调用嵌入生成向量,最后将生成的新向量存储到数据仓库中,从而完成对数据的存学储。
[图片]
5-1-9 其他Embedding嵌入模型的配置与使用
OpenAI的替代方案

Hugging Face文本嵌入模型
Hugging Face本地模型
在某些对数据保密要求极高的场合下,数据不允许传递到外网,过这个时候就可以考虑使用本地的文本嵌入模型-Hugging Face本地嵌入模型,配置的技巧也非常简单,安装langchain-huggingface与sentence-transformers包,命令如下:
pip3 install -U langchain-huggingface sentence-transformers
直接在我们的项目中安装一下
其中langchain-huggingface 是langchain团队基于huggingface封装的第三方社区包,
sentence-transformers是一个用于生成和使用预训练的文本嵌入,基于transformer架构,也是目前使用量最大的本地文本嵌入模型
配置好后,就可以像正常的文本嵌入模型一样使用了,示例:
[图片]
from langchain_huggingface import HuggingFaceEmbeddings

# 拥有一个hugging Face 本地的文本嵌入模型

embeddings = HuggingFaceEmbeddings()

query_vector = embeddings.embed_query("你好，我是Robin，我喜欢打篮球游泳")

print(query_vector)
print(len(query_vector)) # 768

打印：
一共768个向量
[图片]
打开 huggingface 的官网看一下
https://huggingface.co/
下载一个对应的试一下， 这里就不试了
HuggingFace远程嵌入模型
部分模型的文件比较大,如果只是短期内调试,可以考虑使用HuggingFace提供的远程嵌入模型,首先安装对应的依赖:
pip3 install huggingface_hub

Huggingface settings 中创建 Token
然后在Hugging Face官网(https://huggingface.co/)的setting中添加对应的访问秘钥,并配置到.env文件中
HUGGINGFACEHUB_API_TOKEN=XXX
在 .env 中配置一下
[图片]
接下来就可以使用Hugging Face提供的推理服务,这样在本地服务器上就无需配置对应的文本嵌入模型了。
import dotenv
from langchain_huggingface import HuggingFaceEndpointEmbeddings

dotenv.load_dotenv()

embeddings = HuggingFaceEndpointEmbeddings(
model="sentence-transformers/all-MiniLM-L12-v2"
)

query_vector = embeddings.embed_query("你好，我是Robin，我喜欢打篮球游泳")

print(query_vector)
print(len(query_vector))

成功
[图片]
百度干帆文本嵌入模型
[图片]
5-1-10 Faiss向量数据库的配置与使用
目前关于向量数据库的技术进展非常迅速,所以不同服务商提供的向量数据库使用差异非常大,数据的存储结构、支持的相似性检索方式、集合、条件筛选等功能差异也比较大,在LangChain中对于于向量数据库基类只做了通用性的封装,减轻了部分迁移成本,在使用向量数据库时一定要综合衡量下各个向量数据库的差异。
按照部署方式和提供的服务类型进行划分,向最数据库可以划分成几种:

1. 本地文件向量数据库:用户将向量数据存储到本地文件系统中,通过数据库查询的接口来检索向量数据,例如:Faiss
2. 本地部署API向量数据库:这类数据库不仅允许本地部署,而且提供了方便的APl接口,使用户可以通过网络请求来访问和查询向量数据,这类数据库通常提供了更复杂的功能和管理选项,例如:Milvus、Annoy、Weaviate等,
3. 云端API向量数据库:将向量数据存储在云端,通过API提供向量数据的访问和管理功能,例如:TCVectorDB、Pinecone等,
   要想快速上手向量数据库的使用,只需要把向量数据库看成是Excel电子表格使用即可,按照使用办公软件的流程:安装、写入数据、查找数据、删除数据、更新数据、保存数据等相同的流程去学学习+使用向量数据库即可。
   而且向量数据库没有SQL数据库这么多复杂的查询功能,也没有有事务,学习起来其实比绝大部分传统数据库都要容易上手
   Faiss向量数据库简介
   Faiss是Facebook团队开源的向量检索工具,针对高维空间的海量数据,提供高效可靠的相似性检索方式,被广泛用于推荐系统、图片和视频搜索等业务。Faiss支持Linux、macOS和Windows 操作系统,在百万级向量的相似性检索表现中,Faiss能实现<10ms的响应(需牺牲搜索准确度)。
   Faiss官网:https://faiss.ai/, Faiss仓库:https://github.com/facebookresearch/faiss
   Faiss使用C++开发,提供了Python接口,可以通过pip安装Faiss库:
   #CPU环境下使用
   pip3 install faiss-cpu

目前绝大部分向星数据库都支持多种对数据的操作方法:新增数据、检索数据、带得分的数据检索、带筛选条件的数据检索、删除数据等,但是几乎都不支持修改数据,这是因为向量数据库通常使用符定的索引结构(如向量索引树或近似最临投紧算法),这些结构结构需要再数据插入后进行构建和优化,如果允许修改数据,索引结构可能需要频繁更新,这会显著增加系统的复杂性和开销,所以一般是删除后再新增,
Faiss也类似,不过由于Faiss是本地文件向量数据库,还额外支支持了将向量数据持久化到本地、从本地文件夹加载向量数据库等操作。
Faiss向量数据库使用技巧
数据的导入与相似性搜索
在LangChain中,提供了from_texts和from_documents两个通用方法,这两个方法可以快捷从文本和文档中导入数据到向量数据库中,由于向量数据库存储的向量,所以需要传入文本嵌入模型,让向量数据库自动将传入的文本转换成向量
尝试一下
import dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Fix OpenMP library conflict on macOS

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

dotenv.load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")

db = FAISS.from_texts(
[
"肚肚是一只很喜欢睡觉的猫咪",
"我喜欢在夜晚听音乐,这让我感到放松,",
"猫咪在窗台上打盹,看起来非常可爱,",
"学习新技能是每个人都应该追求的日标。",
"我最喜欢的食物是意大利面,尤其是番茄酱的那种。",
"昨晚我做了一个奇怪的梦,梦见自己在太空飞行,",
"我的手机突然关机了,让我有些焦虑,",
"阅读是我每天都会做的事情,我觉得很充实,",
"他们一起计划了一次周末的野餐,希望天气能好,",
"我的狗喜欢追逐球,看起来非常开心。",
],
embedding,
)

print(db.index.ntotal) # 10

# 即返回了10条数据

完成数据的填充后,即可在向量数据库中进行对应的检索,LangChain为所有的向量数据库都设计封装了一致的搜索接口,最常用的有以下4种:

1. similarity_search():基础相似度搜索,传递query(搜索话句)、k(返回条数)、filter(过滤器)、fetch_k(富余条数)等。
2. similarity_search_with_score():携带得分的相似性搜索,参数和similarity_search()函数保持一致,只是会返回得分，这里的得分并不是相似性得分,而是欧几里得距离。
3. similarity_search_with_relevance_scores():携带相关性得分的相似性搜索,得分范围是0-1
4. as_retriever():将向量数据库转换成检索器,检索器是Runnable可运行组件.

然后在刚那段代码中测试一下
print(db.similarity_search_with_score("我养了一只猫，叫肚肚"))
[图片]
然后试一下similarity_search_with_relevance_scores
[图片]
越靠近1越好
但是为什么会有负值呢？
[图片]
是因为源码有问题，distance有可能大于根号2
原理：

[图片]
扩展到三维向量空间中(向量的范围是[0,1]),两个向量/点之间最大距离为√3,并不是√2,所以直接套用公式,可能会出现负数得分,在N维向量空间下,两点的最大距离是√N,所以出现负数的概率大大增加.
可以修改成以下方式进行修正:
def_euclidean_relevance_score_fn(distance: floaat) -> float:
return 1.0 / (1.0 + distance)
因此修改一下，给 from_texts 增加第三个参数
relevance_score_fn=lambda x: 1.0 / (1.0 + x),
[图片]
结果就不会出现小于1的数据了

在使用LangChain封装的向量数据库时,一定要注意测试和校验下文本嵌入横型生成向量的数值范围,避免出现明显的错误。由于向量数据库目前更新太快,而且LangChain封装了太多的第三方组件(数百个),在很多场合下,LangChain可能没有对每一种情况进行测试,有可能会出现一些莫名其妙的计算结果。
带过滤的相似性搜索
在绝大部分向量数据库中,除了存储向量数据,还支持存储对应的元数据,这里的元数据可以是文本原文、扩展信息、页码、归属文档id、作者、创建时间等等任何自定义信息,一般在向最数据库中，会通过元数据来实现对数据的检索。
向量数据库记录 = 向量(vector) + 元数据(metadata) + id
比较遗憾的是Faiss原生并不支持过滤,所以在LangChain封装的FAISS中对过滤功能进行了相应的处理,首先获取比k(返回条数)更多的结果fetch_k(默认为20条),然后先进行搜索,接下再搜索得到的fetch_k结果上进行过滤,得到k条结果,从而实现带过滤的相似性搜索.
为什么要先多取 fetch_k
因为如果你只取 k=4 条，再过滤，可能 4 条里只有 1 条满足条件，最后结果就不够。
比如：

- 你想返回 k=3
- 但限制条件是 page > 5
  Faiss 先找到最相似的 20 条，
  然后 LangChain 再把 page <= 5 的删掉，
  最后从剩下的里取前 3 条。
  所以 fetch_k 太小会导致：
- 过滤后结果不足
- 召回率下降
  而且Faiss 的相似性搜索是针对向量的，过滤是针对元数据的。,在Faiss中执行带过滤的相似性搜索非常简单,只需要在搜索时传递filter多数即可,filter可以传递一个元数据字典,也可以接收一个函数(函数的参数为元数据字典,返回值为布尔值)。

在 LangChain 的 FAISS 里，“带过滤的相似性搜索”本质是：
先用 Faiss 按向量相似度找出较多候选结果，再用 metadata 条件做二次筛选，最后返回前 k 条。

例如下方的代码只会对page>5的文档进行检索,代码如下:
import os
import dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Fix OpenMP library conflict on macOS

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

dotenv.load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")

metadatas: list = [
{"page": 1},
{"page": 2},
{"page": 3},
{"page": 4},
{"page": 5},
{"page": 6},
{"page": 7},
{"page": 8},
{"page": 9},
{"page": 10},
]

db = FAISS.from_texts(
[
"肚肚是一只很喜欢睡觉的猫咪",
"我喜欢在夜晚听音乐,这让我感到放松,",
"猫咪在窗台上打盹,看起来非常可爱,",
"学习新技能是每个人都应该追求的日标。",
"我最喜欢的食物是意大利面,尤其是番茄酱的那种。",
"昨晚我做了一个奇怪的梦,梦见自己在太空飞行,",
"我的手机突然关机了,让我有些焦虑,",
"阅读是我每天都会做的事情,我觉得很充实,",
"他们一起计划了一次周末的野餐,希望天气能好,",
"我的狗喜欢追逐球,看起来非常开心。",
],
embedding,
metadatas=metadatas,
relevance_score_fn=lambda x: 1.0 / (1.0 + x),
)

# print(db.index.ntotal) # 10

# 即返回了10条数据

# print(db.similarity_search_with_score("我养了一只猫，叫肚肚"))

# print(db.similarity_search_with_relevance_scores("我养了一只猫，叫肚肚"))

# 在相似性搜索的时候传递filter参数

print(
db.similarity_search_with_relevance_scores(
"我养了一只猫，叫肚肚", filter=lambda x: x["page"] > 5
)
) # 找到的数据的page都大于5

print(db.index_to_docstore_id) # 打印每一项的唯一值

[图片]
删除指定数据
在Faiss中,支持删除向量数据库中特定的数据,目前仅支持传入数据条目id进行删除,并不支持条件筛选(但是可以通过条件筛选找到符合的数据,然后提取id列表,然后批量删除)。
print("删除前数量:", db.index.ntotal)

# 获取向量数据库的索引id列表信息

db.delete([db.index_to_docstore_id[0]])
print("删除后数量:", db.index.ntotal)

# 删除前数量: 10

# 删除后数量: 9

保存和加载本地数据
除了从文本和文档列表中加载数据到向量数据库,Faiss还支持多整个数据库持久化到本地文件,亦或者从本地文件一键加载数据,这样就不需要在每次使用向量数据库的时候重新创建,可以极大提升向量数据库的使用效率,两个方法如下:

1. save_local():将向量数据库持久化到本地,传递folder_path和index分别代表文件夹路径与索引名字。
2. load_local():将本地的数据加载到向量数据库,传递folder_path、embeddings和index分别代表文件夹路径、嵌入模型索引名字,
   [图片]
   5-1-11 Pinecone向量数据库的配置与使用
   Pinecone 向量数据库简介
   Pinecone是一个托管的、云原生的向量数据库,具有极简的API,并且无需在本地部署即可快速使用,Pinecone服务提供商还为每个账户设置了足够的免费空间,在开发阶段,可以快速基于Pinecone快速开发AI应用。
   相关资料:
3. Pinecone官网:https://www.pinecone.io/
4. Pinecone翻译文档:https://www.pinecone-io.com/
5. langchain-pinecone 翻译文档:http://imooc-langchain.shortvar.com/docs/integrations/vectorstores/pinecone/
   Pinecone向量数据库的设计架构与Faiss差异较大,Pinecone由于是一个面向商业端的向量数据库,在功能和概念上会更加丰富,有几个核心概念+架构图如下:
   [图片]
   概念的解释如下:
6. 组织:组织是使用相同结算方式的一个或者多个项目的集合,例如个人账号、公司账号等都算是一个组织。
7. 项目:项目是用来管理向量数据库、索引、硬件资源等内容的整合,可以将不同的项目数据进行区分。
8. 索引:索引是Pinecone中数据的最高组织单位,在索引中需要定义向量的存储维度、查询时使用的相似性指标,并且在Pinecone中支持两种类型的索引:无服务器索引(根据数据大小自动扩容)和Pod索引(预设空间/硬件)
9. 命名空间:命名空间是索引内的分区,用于将索引中的数据区分成不同的组,以便于在不同的组内存储不同的数据,例如知识库、记忆的数据可以存储到不同的组中,类似Excel中的sheet表。
10. 记录:记录是数据的基本单位,一条记录涵盖了ID、向量(values)。元数据(metadata)等
    所以在Pinecone中使用向量数据库,要确保组织、项目、索引、命名空间、记录等内容均配置好才可以使用,并且由于Pinecone是云端向量数据库,使用时还需配置对应的API秘钥(可在注册好Pinecone后管理页面的API Key中设置)。
    对于Pinecone,LangChain团队也封装了相应的包,安装命令:
    pip install -U langchain-pinecone
    然后在.env文件中配置对应的API密钥,如下:

# Pinecone向量数据库

PINECONE_API_KEY=XXX
接下来就可以像Faiss一样去使用LangChain封装好的向量数据库了(会有稍许差异,这是不同向量数据库之间的一些差异)。

访问Pinecone，然后记录API KEY
然后创建索引
[图片]
然后安装python的必要包
pip3 install langchain-pinecone
然后配置API秘钥，在.env之下

Pinecone向最数据库使用技巧
数据的导入
Pinecone和Faiss一样拥有from_texts和from_documents方法,支持快捷从文本列表和文档列表中构建向量数据库,也支持通过构造函数实例化Pinecone向量数据库后,通过add_texts的方式添加数据。
在配置好Index(llmops)、namespace(**default**)、api_key后,可执行以下代码完成向量数据库数据的添加:

为什么既需要“文本列表 / documents 列表”，又需要 metadatas 列表？
答案是：因为它们职责不一样。

- 文本列表：用来生成向量，做相似性检索
- metadatas 列表：用来存附加信息，做过滤、追踪来源、展示上下文
  一条记录 = text + vector + metadata + id
  操作一下：
  import dotenv
  from langchain_openai import OpenAIEmbeddings
  from langchain_pinecone import PineconeVectorStore

dotenv.load_dotenv()

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
db = PineconeVectorStore(
index_name="llmops", embedding=embedding, namespace="**default**"
)

metadatas: list = [
{"page": 1},
{"page": 2},
{"page": 3},
{"page": 4},
{"page": 5},
{"page": 6},
{"page": 7},
{"page": 8},
{"page": 9},
{"page": 10},
]

db.add_texts(
[
"肚肚是一只很喜欢睡觉的猫咪",
"我喜欢在夜晚听音乐,这让我感到放松,",
"猫咪在窗台上打盹,看起来非常可爱,",
"学习新技能是每个人都应该追求的日标。",
"我最喜欢的食物是意大利面,尤其是番茄酱的那种。",
"昨晚我做了一个奇怪的梦,梦见自己在太空飞行,",
"我的手机突然关机了,让我有些焦虑,",
"阅读是我每天都会做的事情,我觉得很充实,",
"他们一起计划了一次周末的野餐,希望天气能好,",
"我的狗喜欢追逐球,看起来非常开心。",
],
metadatas,
namespace="**default**",
)

print(db.similarity_search_with_relevance_scores("我养了一只猫，叫肚肚"))

返回，成功的执行了相似性搜索
[图片]
执行完之后我们再看
[图片]
10条数据都插入进去了
带过滤的相似性搜索
和Faiss不同,Pinecone支持原生的带过滤的相似性检索功能(元数据筛选),使用元数据过滤器会精确检索与过滤器匹配的最临近结果数,在Pinecone中,过滤器格式为json,其中键是元数据字段对应字符串,值是字符串、数字、布尔值、列表、json中的一种。
例如下方是精确筛选的过滤器:
[图片]
除此之外,筛选器的值还可以传递json数据,用于支持更加复杂的条件搜索,而且还可以和AND/OR配合,
[图片]
例如检索页数小于等于5页的数据：

# 检索例如检索页数小于等于5页的数据：

print(
db.similarity_search_with_relevance_scores(
"我养了一只猫，叫肚肚", filter={"page": {"$lte": 5}}
)
)

筛选成功：
[图片]
[图片]
删除指定数据
[图片]
获取原始实例
[图片]
5-1-12 TCVectorDB向量数据库的配置与使用
TCVectorDB向量数据库简介
虽然目前绝大部分开源向量数据库都是海外的,配置起来也非常简单,性能也很高,但是因为网络的原因,如果将向量数据库部署到海外,而产品面向国内,网络延迟是一个必要考虑的问题,所以考虑国内服务提供商的云向量数据库往往是最佳的选择。
腾讯云向量数据库(TCVectorDB)是一款全托管的自研企业级分布式数据库服务,专用于存储、检索、分析多维向量数据,该数据库支持多种索引类型和相似度计算方法,索引支持千亿级向量规模,可支持百万级QPS及毫秒级查询延迟,而且目前认证过的腾讯云账号可以免费使用TCVectorDB一个月时间,相关文档:

1. TCVectorDB产品链接:https://cloud.tencent.com/product/vdb
2. TCVectorDB产品文档:https://cloud.tencent.com/document/product/1709
3. LangChainTCVectorDB翻译文档:http://imooc-langchain.shortvar.com/docs/integrations/vectorstores/tencentvectordb/
   TCVectorDB和Pinecone的设计理念非常接近,在腾讯云向量数据库中也有对应的数据库、集合、记录等概念:
4. 数据库:分为普通向量数据库和Al数据库,其中Al数据库无需外部配置文本分割、Embedding、文档解析等功能,底层全部又腾讯云实现,而普通向量数据库则需要外部程序处理,它只能接收传递的数据,并没有处理功能,但是功能更加可定制化。
5. 集合:集合是数据库的下一个单位,类似于传统数据库中的表,在集合中,需要设置集合名称、分片数、索引等信息。
6. 记录:集合的每一条数据就是记录。
   TCVectorDB默认只能在内网中链接使用,在生产环境中,也尽可能不将数据库暴露到外网中,但是在开发中,则需要配置并开外网访问功能,配置好外网访问功能、API秘钥后,需要在项目中导入对应的环境变量。
   TC_VECTOR_OB_URL=XXX
   TC_VECTOR_DB_USERNAME=100T
   TC_VECTOR_DB_KEY=XXX
   TC_VECTOR_DB_DATABASE=11mops
   TC_VECTOR_DB_TIMEOUT=30
   安装：
   pip3 install tcvectordb
   [图片]
   由于腾讯向量数据库需要额外付费，这节课弃
   5-1-13Weaviate向量数据库的配置与使用
   Weaviate介绍
   Weaviate是完全使用Go语言构建的开源向量数据库,提供了强大的数据存储和检索功能。并且Weaviate提供了多种部署方式以满足不同用户种用例的需求,部署方式如下:
7. Weaviate云:使用Weaviate官方提供的云服务,支持数据复制、零停机更新、无缝扩容等功能,适用于评估、开发和生产场景
8. Docker部署:使用Docker容器部署Weaviate向量数据库,适用于评估和开发等场景。
9. K8S部署:在K8s上部署Weaviate向量数据库,适用于开发和生产场景。
10. 嵌入式Weaviate:基于本地文件的方式构建Weaviate向量搜库,适用于评估场景,不过嵌入式Weaviate只适用于Linux macOS系统,在Windows下不支持.
    Weaviate和Pinecone/TGVectorDB一样,也存在着集合的概念,在Weaviate中集合类似传统关系型数据库中的表,负责管理一类数据/数据对象,要使用Weaviate的流程其实也非常简单:
11. 创建部署Weaviate数据库(使用Weaviate云、Docker部署)。
12. 安装Python客户端/LangChain集成包.
13. 连接Weaviate(本地连接、云端连接)。
14. 创建数据集/集合(代码创建、可视化管理界面创建),在Weaviate中,集合的名字必须以大写字母开头,并且只能包含字母、数字和下划线,否则创建的时候会出错,和Python的类名规范几乎一致。
15. 添加数据/向量。
16. 相似性搜索/带过滤器的相似性搜索,
    参考资料:
17. Weaviate官网:https://weaviate.io/
18. Weaviate快速上手指南:https://weaviate.io/developers/weaviate/quickstart
19. LangChain Weaviate集成包翻译文档:https://imooc-langchain.shortvar.com/docs/integrations/vectorstores/weaviate
    Weaviate云服务
    Weaviate官方为所有注册登录的账号提供了无限量的Weaviate云服务(免费账号每个实例使用时间最大为14天,付费账户不限时，通过邮箱注册登录Weaviate后,找到后台管理系统的clusters((集群)即可快速创建Weaviate向量数据库实例。
    Weaviate后台管理面板:https://console.weaviate.clouddashboard
    新建集群：llmops-study
    [图片]
    创建好Weaviate云服务器集群后,平台提供了REST和gRPC两种链接方式的地址与API密钥,在客户端中即可快速连接到云服务。
    Docker部署Weaviate向量数据库
    在Docker上部署Weaviate向量数据库非常简单,如果使用默认值，则不需要docker-compose.yml文件来运行镜像(适用于开发场景),安装好Docker之后,执行如下命令:
    docker run -d --name weaviate-dev -p 8080:8080-p 50051:50051
    cr.weaviate.io/semitechnologies/weaviate:1.24.20
    上述的命令就会快速创建一个叫weaviate-dev的容器并在后台运行,该容器暴露了两个端口,8080和50051,其中8080端口为REST接口连接端口、50051为gRPC服务连接端口。
    这里我是使用image来打开的
    services:
    weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.36.8
    command: - --host - 0.0.0.0 - --port - "8080" - --scheme - http
    ports: - "8080:8080" - "50051:50051"
    volumes: - weaviate_data:/var/lib/weaviate
    restart: on-failure:0
    environment:
    QUERY_DEFAULTS_LIMIT: 25
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
    PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
    CLUSTER_HOSTNAME: "node1"

volumes:
weaviate_data:

[图片]
除此之外,使用Docker部署的Weaviate向量数据库服务,还有以下几个常见命令:
[图片]
Weaviate向量数据库使用技巧
创建好Weaviate数据库服务后,接下来就可以安装Python客户端/LangChain集成包,命令如下:
pip install -Uqq langchain-weaviate
下一步如果使用的是Weaviate云服务,可以直接从可视化界面创建collection,亦或者在使用时LangChain自动检测对应的数据集是否存在,如果不存在则直接创建。
然后就可以考虑连接Weaviate服务了,Weaviate框架针对不同同的部署方式提供的不同的连接方法:

1. weaviate.connect_to_local():连接到本地的部署服务,需配置连接URL、端口号。
2. weaviate.connect_to_wcs():连接到远程的Weaviate服务,需配置连接URL、连接秘钥.
   [图片]
   创建好客户端后,接下来可以基于客户端创建LangChain向量数据库实例,在实例化LangChain VectorDB时,需要传递client(客户端)、index_name(集合名字)、text(原始文本的存储键)、emlbedding(文本嵌入模型),如下:

执行添加和搜索：
import dotenv
import weaviate
from weaviate.auth import AuthApiKey
from langchain_openai import OpenAIEmbeddings
from langchain_weaviate import WeaviateVectorStore

dotenv.load_dotenv()

metadatas: list = [
{"page": 1},
{"page": 2},
{"page": 3},
{"page": 4},
{"page": 5},
{"page": 6},
{"page": 7},
{"page": 8},
{"page": 9},
{"page": 10},
]

texts = [
"肚肚是一只很喜欢睡觉的猫咪",
"我喜欢在夜晚听音乐,这让我感到放松,",
"猫咪在窗台上打盹,看起来非常可爱,",
"学习新技能是每个人都应该追求的日标。",
"我最喜欢的食物是意大利面,尤其是番茄酱的那种。",
"昨晚我做了一个奇怪的梦,梦见自己在太空飞行,",
"我的手机突然关机了,让我有些焦虑,",
"阅读是我每天都会做的事情,我觉得很充实,",
"他们一起计划了一次周末的野餐,希望天气能好,",
"我的狗喜欢追逐球,看起来非常开心。",
]

# 创建连接客户端

client = weaviate.connect_to_wcs(
cluster_url="xx.c0.asia-southeast1.gcp.weaviate.cloud",
auth_credentials=AuthApiKey(
"xx"
),
)

embedding = OpenAIEmbeddings(model="text-embedding-3-small")

# 创建langchain向量库实例

db = WeaviateVectorStore(
client=client, index_name="DatasetDemo", text_key="text", embedding=embedding
)

# 添加数据

ids = db.add_texts(texts=texts, metadatas=metadatas)
print(ids)

# 执行相似性搜索

print(db.similarity_search_with_relevance_scores("肚肚"))

成功运行
[图片]
[图片]
同时也set进去了这个collection
[图片]
过滤性搜索：

[图片]

[图片]
5-1-14对接自定义向量数据库的配置与使用
对接自定义向量数据库
向量数据库的发展非常迅猛,几乎间隔几天就有新的向量数据库发布,LangChain不可能将所有向量数据库都进行集成,亦或者封装的包存在这一些bug或错误,这个时候就需要考虑创建自定义向量数据库,去实现特定的方法。
在LangChain实现自定义向量数据库的类有两种模式,一种是继承封装好的数据库类,一种是继承基类VectorStore。前一种一般继承后重写部分方法进行扩展或者修复bug,后面一种是对接新的向量数据库。
[图片]
自定义 VectorStore 示例
要在LangChain中对接自定义向量数据,本质上就是将向量数据库提供的方法集成到add_texts、similarity_search、from_texts方法下,例如自建一个基于内存+欧几里得距离的"向量数据库",示例如下:
略
5-2 第2章 LangChain RAG应用开发组件深入学习
5-2-1 本章介绍
LangChain文档组件与文档加载器

- 学习了解Document组件在RAG应用开发中的作用,并学习LangChain文档加载器的配置与使用。
- 学习掌握LangChain集成的各类文档加载器,涵盖CSV文件加载、HTML网页加载、PDF/文件夹/Markdown加载器以及通用文件加载器的使用。
- 学习掌握封装LangChain自定义文档加载器的使用。

LangChain文档转换器与分割器

- 学习了解LangChain文档转换器的作用与使用场景,涵盖了拆分、合并、过滤、翻译等多个功能。
- 学习掌握LangChain集成的各类文本分割器的使用以及封装自定义文本分割器的技巧,不同模式下选择分割器的思路
- 学习掌握LangChain语义分割器的使用及运行流程,以及语义分割器的使用场合。

VectorStore组件与检索器的使用

- 深入学习VectorStore组件,了解多种相似性搜索的几何意义以及在不同场合下的选择策略。
- 学习掌握LangChain检索器与第三方检索器的配置与使用。
- 学习掌握自定义LangChain检索器的技巧。
  5-2-2 Document组件与文档加载器组件的使用
  Document与文档加载器
  Document类是LangChain中的核心组件,这个类定义了一个文档对象的结构,涵盖了文本内容和相关的元数据,Document也是文档加载器、文档分割器、向量数据库、检索器这几个组件之间交互传递的状态数据
  在LangChain 日版本中,Document还支持lookup检索功能,不过新版本下Document组件只拥有最基础的记录信息功能:
  Document = page_content(页面内容) + metadata(元数据)
  通常一个 Document 至少有两部分：
- page_content：正文内容
- metadata：元数据，比如来源文件名、页码、URL、标题等
  Document(
  page_content="LangChain is a framework for LLM applications...",
  metadata={"source": "intro.pdf", "page": 3}
  )
  在前面的课时中,我们通过手动输入的形式来创建数据,但是在RAG开发中,一般会读取特定来源的数据,而非手动录入数据,例如:本地markdown文件、HTML网页、PDF文档、DOC文档URL链接等多种方式来加载数据,然后再将原始文档按照特定切割成特定大小的文档,最后再将数据存储到向量数据库中,很少会手动录入数据。
  所以在RAG应用外部,一般都会有一个额外的扩展,专门用于处理读取数据-切割数据-存储数据这个流程,并且这个流程非常耗时,例如上传一个30M的文档,需要执行加载/切割/文本嵌入,一般都会使用队列/异步进行处理,架构流程图更新如下:
  [图片]

1. 外部数据被读取进系统
   例如 PDF、CSV、MD、HTML、DOC 等。
2. 这些数据被处理后放进向量库
   图里写的是“加载 + 切割文档 + 转换成向量”。
3. 用户提问时，Retriever 去向量库里找相关内容
   找到的内容会作为 {context} 填进 Prompt。
4. Prompt 连同问题、上下文、历史消息一起发给 LLM
   最后再经过输出解析，得到结构化结果。

文档加载器就是把“不同格式的数据源”统一读成 Document 列表的组件。
图中左下角这些：

- CSV 数据
- PDF 文件
- DOC 文档
- MD 文档
- HTML 网页
  都对应不同的 Loader。
  它们的共同目标不是“回答问题”，而是：
  把外部数据变成 LangChain 能继续处理的 Document。

你可以把图里和 Document / Loader 相关的部分拆成这条主线

1. Loader
   负责读取原始数据
2. Document
   负责承载内容和元信息
3. TextSplitter
   把长 Document 切成小块
4. Embeddings + VectorStore
   把切分后的 Document 存成可检索知识库
5. Retriever
   根据问题召回相关 Document
6. Prompt
   把召回内容塞进 {context}
   所以你学习时，最核心的关系是：
   loader -> Document -> Split -> VectorStore -> Retriever -> Prompt
   在新的架构流程中,文档加载器起到的作用就是从各式各样的数据中提取出相应的信息,并转换成标准的Document组件,从而屏蔽不同类型文件的读取差异。
   在LangChain中所有文档加载器的基类为BaseLoader,封装了统一的5个方法:
7. load()/aload():加载和异步加载文档,返回的数据为文档列表。
8. load_and_split():传递分割器,加载并将大文档按照传入的分割器进行切割,返回的数据为分割后的文档列表
9. lazy_load()/alazy_load():懒加载和异步懒加载文档,返回的是一个迭代器,适用于传递的数据源有多份文档的情况,例如文件夹加载器,可以每次获得最新的加载文档,不需要等到所有文档都加载完毕。
   在LangChain中封装了上百种文档加载器,几乎所有的文件都可以使用这些加载器完成数据的读取,而不需要手动去封装
   [图片]
   TextLoader使用技巧与源码解析
   在LangChain中最简单的加载器组件就是TextLoader,这个加载器可以加载一个文本文件(源码、markdown、text等存储成文本结构的文件,DOC并不是文本文件),并把整个文件的内容读入到一个Document对象中,同时为文档对象的metadata添加source 字段用于记录源数据的来源信息。
   TextLoader使用起来非常简单,传递对应的文本路径即可:
   from pathlib import Path

from langchain_community.document_loaders import TextLoader

file_path = Path(**file**).with_name("e-commerce_data.txt")

# 1.构建加载器

loader = TextLoader(str(file_path), encoding="utf-8")

# 2.加载数据

docs = loader.load()

print(docs)
print(len(docs)) # 1
print(
docs[0].metadata
) # {'source': '/Users/luobin/project/llmops/llmops-api/study/document/e-commerce_data.txt'}

成功运行
5-2-3 LangChain内置文档加载器使用技巧
高频内置文档加载器的使用技巧
在LangChain框架内部,封装了上百种不同类型的文档加载器,涵盖了CSV、目录数据、HTML网页、JSON数据、Markdown数据、PDF文档、Office数据等,每一种文档加载器的整体使用流程者非常接近,分成两步:

1. 传递对应的参数,涵盖文件路径、加载器配置等信息,创建文档加载器实例;
2. 调用.load()函数加载得到文档列表。
   使用上有差异的就是不同的文档加载器在实例化时传递的参数略有差异,加载得到的Document记录的信息存在一些差异,例如:
3. CSVLoader:除了传递文件路径,还可以额外传递的参数,例刚如解析指定列、数据来源列、分隔符符号等。
4. DirectoryLoader:传递目录路径,需要解析的文件夹下的文件列表等。
5. JSONLoader:传递文件路径,提取json数据的指定结构表达式等
   LangChain内置文档加载器文档:https://imooc-langchain.slhortvar.com/docs/integrations/document_loaders/
   Markdown文档加载器
   Markdown是一种轻量级标记语言,可用于使用纯文本编辑器包建格式化文本。例如课程的电子书就是Markdown格式文件。
   LangChain中封装了一个 UnstructuredMarkdownLoader 对象,要使用这个加载器,必须安装unstructured包,安装命令:
   pip3 install unstructured
   pip3 install markdown
   unstructured包是一款开源非结构化数据的预处理工具,旨在简化和优化结构化和非结构化文档的预处理,并且内置了用于读取和预处理图像和文本文档(如PDF、HTML、Word文档等)的开源组件。
   也是LangChain文档加载器的核心(绝大部分加载器都基于unstructured包进行开发+封装)。
   安装好unstructured包后,就可以和文本加载器一样,直接传递Markdown文档的路径,如下
   from pathlib import Path

from langchain_community.document_loaders import UnstructuredMarkdownLoader

file_path = Path(**file**).with_name("test.md")

# 1.构建加载器

loader = UnstructuredMarkdownLoader(str(file_path))

# 2.加载数据

docs = loader.load()

print(docs)
print(len(docs)) # 1
print(
docs[0].metadata
) # {'source': '/Users/luobin/project/llmops/llmops-api/study/document/test.md'}

UnstructuredMarkdownLoader默认会将整个文件加载到文档中,加载得到的文档列表只有一个元素,在这个元素的page_content中记录了整个Markdown文档的所有内容。
其实在幕后unstructured包的处理中,已经为不同的文本块创建了不同的"元素",默认情况下是全部结合到一起的,但是可以通过传递参数mode="elements"让所有元素全部分离。
[图片]
文档数量：72
但是一般在加载文件为文档时,很少对文档进行相应的拆分操作在文档加载器中执行分割没法保证操作的一致性(没法确保所有传递文档分割的统一性,分割出来的文档块大小不一,使用不便)。
Office文档加载器
除了Markdown文档,另外一种高频使用的数据就是Office文档,在LangChain中也基于unstructured包封装了对应的文档加载器-- UnstructuredExcelLoader、UnstructuredPowerPointLoader, UnstructuredwordDocumentLoader
分别对应Excel、PPT、Word文档加载器,其中不同的加载器需要安装不同的Python包,命令如下:

# UnstructuredExcelLoader加载器包

pip install unstructured openpyxl pandas

# UnstructuredPowerPointLoader加载器包

pip install unstructured python-magic python-pptxx

# UnstructuredwordDocumentLoader加载盟

pip install unstructured
Office类的非结构化文档加载器使用技巧都非常简单,一般来说,传递对应文档的路径即可,如果需要区分文档中的元素,可以在加载器的构造函数中传递mode="elements"即可(但是一般不使用)。

Excel：

[图片]
word：

[图片]

ppt：
[图片]
利用unstructured包提供的办公文档加载能力,配合LLM可以以实现2023年爆火的ChatPDF功能,即上传特定的PDF,让LLM实现对指定的PDF的问答功能。
URL网页加载器
除了本地文件,LangChain还封装了大量加载网络文件的加载器,例如:网页加载器、腾讯云COS对象存储加载器、Bilibili字幕加载器、Notion数据库加载器等,使用技巧和文件加载器大差不差,传递对应的信息构建加载器,然后加载文档即可。
例如如果想加载获取 百度网 网站首页的数据,即可使用webBaseLoader一键加载,示例如下:
from langchain_community.document_loaders importWebBaseLoader
loader = WebBaseLoader("https://baidu.com")
documents = loader.load()
print(documents)
webBaseLoader加载器底层会从HTML网页中加载所有文本(去除HTML标签),并将所有文本进行合并。利用这个加载器其实就可以以快速实现一个基于特定网页问答的聊天机器人。
WebBaseLoader加载器翻译文档:https://imooc-langchain.shortvar.com/docs/integrations/document_loaders/web_base/
通用文件加载器的使用技巧
在实际的LLM应用开发中,由于数据的种类是无穷的,没办法单独为每一种数据配置一个加载器(也不现实),所以对于一些无法判断的数据类型或者想进行通用性文件加载,可以统一使用非结构化文件加载器UnstructuredFileLoader来实现对文件的加载。
UnstructuredFileLoader 是所有 UnstructuredxxLoader J文档类的基类,其核心是将文档划分为元素,当传递一个文件时,库将读取文档,将其分割为多个部分,对这些部分进行分类,然后提取每个部分的文本,然后根据模式决定是否合并(single、pageed、elements)。
UnstructuredFileLoader可以加载多种类型的文件,涵盖了:文本文件、PowerPoint文件、HTML、PDF、图像、
Markdown、Excel、Word等,使用示例如下:
[图片]
结果：

[图片]
不过由于UnstructuredFileLoader加载器提取元数据只记录了source即数据的来源,信息相对较少,所以如果能明确文件的类型,亦或者是一些高频的文件,尽可能使用更精确的文档加载器,记录的内容会更丰富。
例如通过检测文件的扩展名来加载不同的文件加载器,对于没校验到的文件类型,才考虑使用UnstructuredFileLoader,如下:
[图片]
5-2-4自定义LangChain文档加载器使用技巧
自定义加载器使用技巧
对于一些企业的内部数据,例如 数据库、API接口等定制化非常强的数据,如果使用通用的文档加载器进行提取,虽然可以提议记录到相应的信息,但是加载的数据格式或者样式大概率没法满足我们的需求，这个时候就可以考虑实现自定义文档加载器。
例如上节课使用的webBaseLoader文档加载器加载器加载慕课网首页的信息,会提取得到很多空白数据(空格、换行、Tab等),将这类数据通过分割存储到向量数据库中,会极大降低检索与生成的效率和正确性。
代码略
文档加载器扩展思考
在上面的自定义文档加载器中,可以看到1azy_1oad()方法的两个核心步骤就是:读取文件数据、将文件数据解析成Document,并且绝大部分文档加载器都有着两个核心步骤,而且 谈取文件数据这个步骤大家都大差不差。
就像*.md、*.txt、_.py这类文本文件,甚至是_.pdf、\*.doc等这类非文本文件,都可以使用同一个谈取文件数据步骤将文件读
取为二进制内容,然后在使用不同的解析逻辑来解析对应的二进制内容,所以很容易可以得出:
文档加载器=二进制数据读取+解析逻辑
因此,在项目开发中,如果大量配置自定义文档解析器的话,将解析逻辑与加载逻辑分离,维护起来会更容易,而且也更容易复用相应的逻辑(具体使用哪种方式取决于开发)。
这样原先的DocumentLoader运行流程就变成了如下:
[图片]
这样所有DocumentLoader就变成了共用Blob(数据读取),每个加载器内部只实现不同的parse即可,这也是LangChain目前正在设计的新方案,由于目前LangChain在这块尚不完善,并且篇幅较长,我们留到下一节课来讲解。
5-2-5 Blob与BlobParser代替文档加载器
LangChain 中的 Blob 方案
许多文档加载器都涉及到解析文件,此类加载器之间的差异通常源于文件解析方式,而不是文件加载方式。例如,你可以使用open()函数来读取PDF或Markdown文件的二进制内容,但是需要不同的的解析逻辑来将二进制数据转换为文本
在LangChain中也提供了一个类似的解决方案Blob,其灵感来源于Blob webAPI规范(这是前端Web浏览器中定义的相关规范)。
Blob WebAPI规范文档链接:https://developer.mozilla.org/en-US/docs/Web/API/Blob.
该方案下有Blob、BlobLoader和BaseBlobParser三个类,含义如下

1. Blob:LangChain封装的数据对象,通过引用或值表示原始数做据,该类提供一个接口,以表示不同形式具体化的二进制数据,使用该类可以有助于将数据加载器的开发与解析器耦合。
2. BlobLoader:Blob数据加载器,类似DocumentLoader,不过BlobLoader被设计成可以加载任何数据(未来的规划)。
3. Blobparser:Blob数据解析器,用于将传入的Blob数据转换成文档列表。
   在这个方案下,文档加载器的运行流程变成如下:
   [图片]
   例如上节课的需求(加载对应的文本信息,其中每行数据都作为一个Document组件),使用Blob的方案来实现,只需自定义一个解析器并实现lazy_parser()方法即可,示例代码如下:
   from langchain_core.document_loaders.base import BaseBlobParser
   from langchain_core.document_loaders import Blob
   from langchain_core.documents import Document
   from pathlib import Path

from typing import Iterator

file_path = Path(**file**).with_name("miaowu.txt")

class CustomParser(BaseBlobParser):
"""自定义解析器用于将传入的文本二进制数据的每一行解析成document组件。"""

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        line_number = 0
        with blob.as_bytes_io() as f:
            for line in f:
                yield Document(
                    page_content=line,
                    metadata={"source": blob.source, "line_number": line_number},
                )
                line_number += 1

# 1. 加载blob数据

blob = Blob.from_path(str(file_path))
parser = CustomParser()

# 2.解析得到文档数据

documnents = list(parser.lazy_parse(blob))

# 3.输出相应的信息

print(documnents) # 每一行是个文档
print(len(documnents)) # 11
print(
documnents[0].metadata
) # {'source': '/Users/luobin/project/llmops/llmops-api/study/Blob/miaowu.txt', 'line_number': 0}

[图片]
成功输出，通过blob 加 lazy_loader 实现自定义文档加载器的效果

除了 from_path()函数,Blob类还可以在构造时传递data参数,直接从内存中加载内容,而无需从文件中获取,示例如下:
blob=Blob(data="喵喵\r\n喵喵\r\n喵")
Blob数据存储类
LangChain中设计的Blob数据存储类和Blob WebAPI规范定义的类非常接近,拥有以下方法和属性:

1. data:原始数据,支持存储字节、字符串数据。
2. mimetype:文件的mimetype类型。
3. encoding:文件的编码,默认值为utf-8。
4. path:文件的原始路径,支持传递字符串路径或者Path类。
5. metadata:存储的元数据,一般都有Source字段。
6. source():只读函数/属性,用于返回数据的来源。
7. as_string():将数据转换成字符串。
8. as_bytes():将数据转换成字节数据。
9. as_bytes_io():将数据转换成缓冲流字节数据。
10. from_path():从对应的路径中加载Blob数据(文件)。
11. from_data():从对应的原始数据中加载Blob数据(非文件)。

Blob加载器
解析器封装了将二进制数据解析为Document组件所需的逻辑,而Blob加载器则封装了从给定存储位置加载Blob所需的逻辑。不过目前在LangChain中,只集成了一个FilesystemBloader,即文件系统二进制数据加载器。
这个加载器可以加载传入文件夹下的特定文件,代码示例:
from langchain_community.document_loaders.blob_loaaders import FilesystemBlobLoader

loader = FileSystemBlobLoader(".", show_progress=True)
for blob in loader.yield_blobs():
print(blob.source)
[图片]
Blob通用加载器
在上面的示例中,Blob加载器与解析器是分开使用的,其实在LangChain中还封装了一个由BlobLoader与BaseBlobParser组成的类--GenericLoader,这个类旨在提供标准化的方法,让BlobLoader使用更简单,不过目前也仅支持FilesystemBlobLoader。
使用示例如下:
from langchain_community.document_loaders.generic iimport GenericLoader

loader = GenericLoader.from_filesystem(".", glob=".txt",show_progress=True)

for idx,doc in enumerate(loader.lazy_load()):
print(f"当前加载第{idx+1}个文件,文件信息:{doc.metadata}")
[图片]
整体来说,Blob解决方案目前LangChain封装与集成得非常少,如果需要使用Blob的形式来加载文件,目前还需要大量编写加载文件与解析数据的逻辑,效率比较低,不过随着未来LangChain团队封装的Blob解析逻辑越来越多,会逐渐代替DocumentLoader的方案。对于目前的版本来说,大家只需要知道有这个东西即可。
5-2-6文档转换器与字符分割器组件的使用
DocumentTransformer 组件
在LangChain中,使用文档加载器加载得到的文档一般来说存在着几个问题:原始文档太大、原始文档的数据格式不符合需求(需要英文但是只有中文)、原始文档的信息没有经过提炼等问题。
如果将这类数据直接转换成向量并存储到数据库中,会导致在执行相似性搜索和RAG的过程中,错误率大大提升。所以在LLM应用开发中,在加载完数据后,一般会执行多一步转换的过程,即将加载我得到的文档列表进行转换,得到符合需求的文档列表。
转换涵盖的操作就非常多,例如:文档切割、文档属性提取、文档翻译、HTML转文本、重排、元数据标记等都属于转换。
在前面的聊天机器人架构中添加上转换步骤,更新后的 聊天机器人架构/运行流程 如下所示:
[图片]
先加载数据，加载数据之后执行文档的转换，这里的转换就涵盖了文档的切割

在LangChain中针对文档的转换也统一封装了一个基类BaseDocumentTransformer,所有涉及到文档的转换的类均是该类的子类,将大块文档切割成chunk分块的文档分割器也是BaseDocumentTransformer的子类实现。
BaseDocumentTransformer基类封装了两个方法:

1. transform_documents():抽象方法,传递文档列表,返回转换后的文档列表。
2. atransform_documents():转换文档列表函数的异步实现,如果没有实现,则会委托transform_documents()函数实现。
   在LangChain中,文档转换组件分成了两类:文档分割器(使用频率高）、文档处理转换器(使用频率低,老版本写法)。
   并且目前LangChain团队已经将文档分割器这个高频使用的部分单独拆分成一个Python包,哪怕不使用LangChain框架本身进行打开,也可以使用其文本分割包,快速分割数据,在使用前必须执行以下命令安装:
   pip3 install -qU langchain-text-splitters
   对于文本分割器来说,除了继承BaseDocumentTransformer,还单独设置了文本分割器基类Textsplitter,从而去实现更加丰富的功能,
   BaseDocumentTransformer衍生出来的类图:
   [图片]
   字符分割器基础使用技巧
   在文档分割器中,最简单的分割器就是--字符串分割器,这个组件会基于给定的字符串进行分割,默认为\n\n,并且在分割时会尽可能保证数据的连续性。分割出来每一块的长度是通过字符数来衡量的,使用起来也非常简单,实例化CharacterTextsplitter需传递多个参数,信息如下:
3. separator:分隔符,默认为\n\n。
4. is_separator_regex:是否正则表达式,默认为False。
5. chunk_size:每块文档的内容大小,默认为4000。
6. chunk_overlap:块与块之间重叠的内容大小,默认为200。
7. length_function:计算文本长度的函数,默认为len。
8. keep_separator:是否将分隔符保留到分割的块中,默认为False,
9. add_start_index:是否添加开始索引,默认为False,如果是的话会在元数据中添加该切块的起点。
10. strip_whitespace:是否删除文档头尾的空白,默认为True.

如果想将文档切割为不超过500字符,并且每块之间文本重叠50个字符,可以使用characterTextspliter 来实现,代码如下:
