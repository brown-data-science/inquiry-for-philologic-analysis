#!/usr/bin/python

import numpy as np
import pandas as pd
import sys
import string
import csv
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from nltk import pos_tag
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer
import enchant
# import line_profiler


# @profile
def tag2pos(tag, returnNone=False):
    ap_tag = {'NN': wn.NOUN, 'JJ': wn.ADJ,
              'VB': wn.VERB, 'RB': wn.ADV}
    try:
        return ap_tag[tag[:2]]
    except:
        return None if returnNone else ''
    sys.stdout.write('tag2pos done')
    sys.stdout.write('\n')


# @profile
def lemmatize_pos(x):
    tags = pos_tag(x)
    lemmas = []
    for tag in tags:
        word = str(tag[0])
        word_tag = tag[1]
        word_pos = tag2pos(word_tag)
        if word_pos is not '':
            lemmas.append(lemmatizer.lemmatize(word, word_pos))
        else:
            lemmas.append(lemmatizer.lemmatize(word))
    return(lemmas)
    sys.stdout.write('lemmatize_pos done')
    sys.stdout.write('\n')


# @profile
def prepare_text(text):
    # get year from date
    text['YEAR'] = text.DATE.str[:4]
    sys.stdout.write('get year from date!')
    sys.stdout.write('\n')
    # convert years column to numeric
    text['YEAR'] = text['YEAR'].astype(float)
    sys.stdout.write('convert years column to numeric!')
    sys.stdout.write('\n')
    # fix problems with dates and remove non-alpha numeric characters from debate titles
    for index, row in text.iterrows():
        # fix years after 1908
        if row['YEAR'] > 1908:
            text.loc[index, 'YEAR'] = np.NaN
        # # compute decade
        # # text['DECADE'] = (text['YEAR'].map(lambda x: int(x) - (int(x) % 10)))
        # remove non-alpha numeric characters from bill titles
        text.loc[index, 'BILL'] = str(row.BILL).translate(None, string.digits + string.punctuation)
        # convert integer speech acts to string and decode unicode strings
        if type(row['SPEECH_ACT']) != str and type(row['SPEECH_ACT']) != unicode:
            text.loc[index, 'SPEECH_ACT'] = str('')
        elif type(row['SPEECH_ACT']) is unicode:
            text.loc[index, "SPEECH_ACT"] = row["SPEECH_ACT"].decode('utf-8')
    sys.stdout.write('fix problems with dates, debate titles, unicode!')
    sys.stdout.write('\n')
    # filter out nan speech act rows
    text = text[pd.notnull(text['SPEECH_ACT'])]
    sys.stdout.write('drop NaN speech acts!')
    sys.stdout.write('\n')
    # forward fill missing dates
    text['YEAR'].fillna(method='ffill', inplace=True)
    text['DATE'].fillna(method='ffill', inplace=True)
    sys.stdout.write('forward fill dates!')
    sys.stdout.write('\n')
    # concatenate BILL and DATE to get new DEBATE ID
    text['BILL'] = text['BILL'] + ' ' + text['DATE']
    sys.stdout.write('bill and date ID created!')
    sys.stdout.write('\n')
    # drop some columns
    text.drop(['ID', 'DATE', 'MEMBER', 'CONSTITUENCY'], axis=1, inplace=True)
    sys.stdout.write('hansard corpus processed succesfully!')
    sys.stdout.write('\n')

    # append seeds to text
    with open(path_seed + 'four_corpus.txt', 'r') as f:
        seed = pd.read_csv(f, sep='\t', header=None, names=['SPEECH_ACT'])
    # decode unicode string with unicode codec
    for index, row in seed.iterrows():
        seed[index, "SPEECH_ACT"] = row["SPEECH_ACT"].decode('utf-8')
    # make metadataframe for seeds
    seed['BILL'] = ['Seed1-Napier', 'Seed2-Devon',
                    'Seed3-Richmond', 'Seed4-Bessborough']
    seed['YEAR'] = [1884, 1845, 1882, 1881]
    seed = seed[['BILL', 'YEAR', 'SPEECH_ACT']]
    # append to end of text df
    text = pd.concat([text, seed]).reset_index(drop=True)

    # remove tabs from text columns
    # remove quotes too?

    # write to csv
    text.to_csv(path + 'membercontributions-20170824.tsv', sep='\t', index=False)
    sys.stdout.write('corpus and seed processed and written successfully!')
    sys.stdout.write('\n')

    return(text)


# function to build up dictionary of all unique words and replace words in corpus with stems
# @profile
def build_dict_replace_words(row, mdict, custom_stopwords):

    # get unique words in speech act
    vectorizer = CountVectorizer()
    vec = vectorizer.fit_transform([row[2]])
    words = vectorizer.get_feature_names()
    sys.stdout.write('count vectorizer and fit transform!')
    sys.stdout.write('\n')

    # check dictionary for words and add if not present
    # check if word is already in dict
    not_cached = [word for word in words if word not in mdict]
    # check if word is stopword, dummy, or not dummy
    dictionary = enchant.Dict("en_GB")
    stopword = [word for word in not_cached if word in custom_stopwords]
    stopword_dict = dict(zip(stopword, ['stopwordstop'] * len(stopword)))
    dummy = [word for word in not_cached if word not in custom_stopwords and
             word.isalpha() is False or dictionary.check(word) is False]
    dummy_dict = dict(zip(dummy, ['williewaiola'] * len(dummy)))
    # stem or lemmatize
    not_dummy = [word for word in words if word not in custom_stopwords and
                 word.isalpha() and
                 dictionary.check(word)]
    stems = [stemmer.stem(word) for word in not_dummy]
    # TOFIX: lemmas = lemmatize_pos(not_dummy)
    not_dummy_dict = dict(zip(not_dummy, stems))
    # update dictionary
    mdict.update(stopword_dict)
    mdict.update(dummy_dict)
    mdict.update(not_dummy_dict)
    sys.stdout.write('number of keys in master dict = {}'.format(len(mdict)))
    sys.stdout.write('\n')

    # replace words with stems or dummy
    veca = vec.toarray()
    # write metadata to file for mallet
    with open(path + "../debates/mc-20170824-stemmed.txt", "a") as f:
        f.write(str(row[0]) + '\t' + str(row[1]) + '\t')
    # write speech act with stems or dummy
    for i in range(len(words)):
        with open(path + "../debates/mc-20170824-stemmed.txt", "a") as f:
            f.write((str(mdict.get(words[i])) + ' ') * int(veca[:, i]))
    # insert new line character after each speech act
    with open(path + "../mc-20170824-stemmed.txt", "a") as f:
        f.write('\n')
        sys.stdout.write('speech act {} written to file'.format(index))
        sys.stdout.write('\n')


# Function to read dataframe and read empty df if no columns
def read_data(file):
    try:
        df = pd.read_csv(file, sep='\t', skiprows=row.SEQ_IND, usecols=[2],
                         quoting=csv.QUOTE_NONE)
    #except pd.io.common.EmptyDataError:
    except IOError:
        sys.stdout.write('cannot read speech act into dataframe')
        sys.stdout.write('\n')
        df = pd.DataFrame()
    return df


# function to count correctly spelled and incorrectly spelled words
# @profile
def count_words(row, mdict):
    # read sa from file and create sa vector
    #with open(path + '../debates/mc-20170824-stemmed.txt', 'r') as f:
    #    sa = pd.read_csv(f, sep='\t', skiprows=row.SEQ_IND, usecols=[2],
    #                     quoting=csv.QUOTE_NONE)
    sa = read_data(path + '../mc-20170824-stemmed.txt')
    vectorizer2 = CountVectorizer(vocabulary=mdict)
    vec2 = vectorizer2.fit_transform(sa)
    if sa.shape[0] > 0:
        dummy_ind = vectorizer2.vocabulary_.get('williewaiola')
        stopword_ind = vectorizer2.vocabulary_.get('stopwordstop')
        vec2 = vec2.toarray()
        sys.stdout.write('speech act {} added to debate {} matrix'.format(row.SEQ_IND, name))
        sys.stdout.write('\n')
    else:
        dummy_ind = 0
        stopword_ind = 0
        vec2 = np.zeros((1, len(mdict)))
        sys.stdout.write('speech act {} EMPTY and zeroes added to debate {} matrix'.format(row.SEQ_IND, name))
        sys.stdout.write('\n')

    return(vec2, dummy_ind, stopword_ind)


# Set the paths
path = '/gpfs/data/datasci/paper-m/data/speeches_dates/'
path_seed = '/gpfs/data/datasci/paper-m/data/seed/'
# path = '/users/alee35/Google Drive/repos/inquiry-for-philologic-analysis/data/'
# path_seed = '/users/alee35/Google Drive/repos/inquiry-for-philologic-analysis/data/'
sys.stdout = open('../logs/log.txt', 'w')

# Load the raw data to a dataframe
#with open(path + 'membercontributions-20161026.tsv', 'r') as f:
#    text = pd.read_csv(f, sep='\t')
# with open(path + 'membercontributions_test.tsv', 'r') as f:
   # text = pd.read_csv(f, sep='\t')
#sys.stdout.write('corpus read in successfully!')
#sys.stdout.write('\n')

# Prepare the Text
#text = prepare_text(text)

# Read from csv after doing prepare_text once
with open(path + 'membercontributions-20170824.tsv', 'r') as f:
   text = pd.read_csv(f, sep='\t')
sys.stdout.write('corpus read in successfully!')
sys.stdout.write('\n')
print(text.isnull().sum())

# Remove rows with missing speech acts
text = text[pd.notnull(text.SPEECH_ACT)]

# Concatenate speech acts to full debates
deb = text.groupby(['BILL', 'YEAR'])['SPEECH_ACT'].agg(lambda x: ' '.join(x)).reset_index()
sys.stdout.write('speech acts successfully concatenated!')
sys.stdout.write('\n')
print(deb.isnull().sum())
for index, row in deb.iterrows():
    print(row['BILL'])

# # Initialize a dictionary of all unique words, stemmer and lemmatizer
# master_dict = {}
# stemmer = SnowballStemmer('english')
# lemmatizer = WordNetLemmatizer()

# # Read in custom stopword lists
# with open('../data/stoplists/en.txt') as f:
#     en_stop = f.read().splitlines()
# with open('../data/stoplists/stopwords-20170628.txt') as f:
#     custom_stop = f.read().splitlines()
# custom_stopwords = en_stop + custom_stop
# sys.stdout.write('custom stopword list created successfully!')
# sys.stdout.write('\n')

# # Write stemmed corpus to file
# for index, row in deb.iterrows():
#     print(row)
#     build_dict_replace_words(row, master_dict, custom_stopwords)

# # Pickle Master Dictionary to check topic modeling later
# with open(path + 'master_dict.pickle', 'wb') as handle:
#     pickle.dump(master_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
# # Load and deserialize pickled dict
# # with open(path + 'master_dict.pickle', 'rb') as handle:
# #     master_dict = pickle.load(handle)
# sys.stdout.write('master dictionary pickled successfully!')
# sys.stdout.write('\n')

# # Vocabulary for counting words is unique set of values in master dict
# vocabulary = set(master_dict.values())
# sys.stdout.write('vocabulary built successfully!')
# sys.stdout.write('\n')

# # Count words and build debate doc-term matrix
# group = text.groupby(["BILL"], sort=False)
# doc_term_matrix = np.zeros((len(group), len(vocabulary)), dtype=int)

# group_ind = 0
# for name, df in group:
#     # need debate index, speech act index, and sa within debate index
#     # group_ind = group.indices.get(name)     # debate index
#     print("group_ind: " + str(group_ind))
#     seq_ind = df.index.tolist()             # sa index
#     df = df.assign(SEQ_IND=seq_ind)
#     df.reset_index(inplace=True)            # sa w/i debate index
#     # initialize debate matrix
#     num_docs = df.shape[0]
#     debate_matrix = np.zeros((num_docs, len(vocabulary)), dtype=int)
#     # fill debate matrix, speech act by speech act
#     for index, row in df.iterrows():
#         sa_vec, dummy_ind, stopword_ind = count_words(row, vocabulary)
#         debate_matrix[index, ] = sa_vec
#     # sum debate matrix rows to get debate vector
#     debate_vec = debate_matrix.sum(axis=0)
#     # build document term matrix, debate by debate
#     doc_term_matrix[group_ind, ] = debate_vec
#     # add one to debate index
#     group_ind += 1
# sys.stdout.write('doc-term matrix built successfully!')
# sys.stdout.write('\n')

# # Print number of correctly/incorrectly spelled words
# nr_stopwords = doc_term_matrix[:, stopword_ind].sum()
# nr_incorrectly_sp = doc_term_matrix[:, dummy_ind].sum()
# nr_correctly_sp = doc_term_matrix.sum() - nr_incorrectly_sp
# sys.stdout.write('Number stopwords: ' + str(nr_stopwords))
# sys.stdout.write('\n')
# sys.stdout.write('Number incorrectly spelled: ' + str(nr_incorrectly_sp))
# sys.stdout.write('\n')
# sys.stdout.write('Number correctly spelled: ' + str(nr_correctly_sp))
# sys.stdout.write('\n')
