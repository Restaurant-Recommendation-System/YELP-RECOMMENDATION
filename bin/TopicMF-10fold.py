import random 
import math
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import NMF
from sklearn.utils.extmath import randomized_svd
from sklearn.decomposition import TruncatedSVD
from scipy.sparse.linalg import svds
from sklearn.metrics import mean_squared_error

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
from nltk.stem.porter import PorterStemmer

def prep(doc):
    raw = doc.lower().replace("\n", "").replace("\t", "")
    tokens = tokenizer.tokenize(raw)
    stopped_tokens = [i for i in tokens if not i in en_stop]
    # texts = [p_stemmer.stem(i) for i in stopped_tokens]
    texts = stopped_tokens
    return (" ").join(texts)

from sklearn import linear_model
def MLR(X, Y):
    reg = linear_model.LinearRegression()
    reg.fit(X, Y)
    return reg.coef_


f = open('new_5k/5k-data', 'r')
business_name = eval(f.readline())
business_avg = eval(f.readline())
user_name = eval(f.readline())
user_avg = eval(f.readline())

# f = open('../new_5k/5k-relation', 'r').read()
# relation = eval(f)

f = open('new_5k/5k-review', 'r')
review5k_business = eval(f.readline())
review5k_user = eval(f.readline())
review5k_rating = eval(f.readline())
review5k_text = eval(f.readline())

#f7 = open('relation_5k', 'r').read()
#relation = eval(f7)

print "read file..."

fold_size = len(review5k_rating) / 10

total_ubb = 0
total_BasicPd = 0
total_TopicInPd = []
for n in xrange(10):
    total_TopicInPd.append([])

for fold in range(10):
    print "%s fold: " % (fold)
    # random_test = random.sample(xrange(len(review5k_rating)), 1000)

    train_user = []
    train_business = []
    train_rating = []
    train_text = []

    test_user = []
    test_business = []
    test_rating = []

    
    for r in xrange(len(review5k_rating)):
        if ( fold * fold_size < r and r < (fold+1) * fold_size  ):
            test_user.append(review5k_user[r])
            test_business.append(review5k_business[r])
            test_rating.append(review5k_rating[r])
        else:
            train_user.append(review5k_user[r])
            train_business.append(review5k_business[r])
            train_rating.append(review5k_rating[r])
            train_text.append(review5k_text[r])
        
    K_topic = 10
    Times = 50
    DocWord = 300
    DocTopic = 5

    num_user = len(user_avg)
    num_business = len(business_avg)
    num_train = len(train_rating)
    num_test = len(test_rating)

    mu = np.mean(train_rating)

    tokenizer = RegexpTokenizer(r'\w+')
    en_stop = get_stop_words('en')
    p_stemmer = PorterStemmer()

    print " Ubb Model",

    Ubb = []
    for i in xrange(num_user):
        Ubb.append([])
        for j in xrange(num_business):
            val = user_avg[i] + business_avg[j] - mu
            if val < 1: val = 1
            if val > 5: val = 5
            Ubb[i].append(val) 

    UbbPd = []
    for r in xrange(num_test):
        UbbPd.append(Ubb[test_user[r]][test_business[r]]) 

    Ubb_rmse = mean_squared_error(test_rating, UbbPd)  

    print Ubb_rmse

    print " Topic Model",

    BasicIn = []
    for i in xrange(num_user):
        BasicIn.append([])
        for j in xrange(num_business):
            val = user_avg[i] + business_avg[j] - mu
            if val < 1: val = 1
            if val > 5: val = 5
            BasicIn[i].append(val) 
        
    for r in xrange(num_train):
        BasicIn[train_user[r]][train_business[r]] = train_rating[r]

    model = NMF(n_components=K_topic, init='random', random_state=0)
    U = model.fit_transform(BasicIn);
    V = model.components_;
    BasicOut = np.dot(U,V)

    BasicPd = []
    for r in xrange(num_test):
        BasicPd.append(BasicOut[test_user[r]][test_business[r]]) 

    BasicPd_rmse = mean_squared_error(test_rating, BasicPd)  

    print BasicPd_rmse

    Breview = [""]*num_business
    for r in xrange(num_train):
        Breview[train_business[r]] += prep(train_text[r])

    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=DocWord, stop_words='english')
    tf = tf_vectorizer.fit_transform(Breview)

    lda = LatentDirichletAllocation(n_topics=DocTopic, max_iter=5, learning_method='online',learning_offset=50.,random_state=0)
    DocTopDist = lda.fit_transform(tf)

    row = np.array([])
    col = np.array([])
    val = np.array([])

    # delta -> difference between rating and ubb [u*b], delta2 -> rating boolean
    delta = csr_matrix((val,(row,col)), shape=(num_user,num_business)).toarray()
    delta2 = csr_matrix((val,(row,col)), shape=(num_user,num_business)).toarray()
    for r in xrange(num_train):
        delta[train_user[r]][train_business[r]] = train_rating[r] - Ubb[train_user[r]][train_business[r]]
        delta2[train_user[r]][train_business[r]] = 1

    deltaReg = []
    for i in xrange(num_user):
        X = [[0,0,0,0,0], [1,0,0,0,0], [0,1,0,0,0], [0,0,1,0,0], [0,0,0,1,0], [0,0,0,0,1]]; Y = [0,0,0,0,0,0]
        for j in xrange(num_business):
            if delta2[i][j]:
                X.append(list(DocTopDist[j]))
                Y.append(delta[i][j])
        coef = MLR(X, Y)
        deltaReg.append(np.dot(DocTopDist, coef))
    
    for n in xrange(10):
        lbd0 = 0.1*(n+1) # optimize
        print " Basic Model lbd =", lbd0,

        row = np.array([])
        col = np.array([])
        val = np.array([])
        TopicIn = csr_matrix((val,(row,col)), shape=(num_user,num_business)).toarray()
        for i in xrange(num_user):
            for j in xrange(num_business):
                val = Ubb[i][j] + lbd0*deltaReg[i][j]
                if val < 1: val = 1
                if val > 5: val = 5
                TopicIn[i][j] = val

        TopicInPd = []
        for r in xrange(num_test):
            TopicInPd.append(TopicIn[test_user[r]][test_business[r]]) 

        TopicInPd_rmse = mean_squared_error(test_rating, TopicInPd)  
        total_TopicInPd[n].append(TopicInPd_rmse)

        print total_TopicInPd[n][fold]
    
    total_ubb += Ubb_rmse
    total_BasicPd += BasicPd_rmse

print "Avg_Ubb_rmse =", total_ubb / 10
print "Avg_BasicPd_rmse =", total_BasicPd / 10
for n in xrange(10):
    print 0.1*(n+1),
    print sum(total_TopicInPd[n]) / 10
