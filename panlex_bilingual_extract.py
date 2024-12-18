#author: Di Lu
# -*- coding: utf-8 -*-                                                                                                  
import argparse
import sqlite3 as lite
import sys
from lxml import etree
import xml.etree.ElementTree as ET
import os
import json
def langid_extract(source_language, target_language, panlex_dir):
        source_langid = None
        target_langid = None
        wiktionary_file= os.path.join(panlex_dir, 'langvar.json')
        with open(wiktionary_file) as f:
                lines = f.read()
        json_lines = json.loads(lines)
        for line in json_lines:
                if line['lang_code'] == source_language and line['var_code'] == 0:
                        source_langid = str(line['id'])
                if line['lang_code'] == target_language and line['var_code'] == 0:
                        target_langid = str(line['id'])
        return source_langid, target_langid


def extract_bilingual_lexicon(source_language, target_language, source_langid, target_langid, output_directory, sql_database):
        #(il,hlx,il_lang_id,hl_lang_id,path_output)

        
    con = lite.connect(sql_database)

    with con:
        print('loading expression file')

        n=0
        ll={}
        hl={}
        llm={}
        hlm={}
        mention_dic={}
        nsmap = {}
        expr_dic={}
        cur = con.cursor()
        cur.execute("SELECT * FROM Exprs")
        while True:
            row = cur.fetchone()
            if row == None:
                break
            expr_dic[row[1]]=row[2]
            if row[2]==source_langid:
                ll[row[1]]=row[3].encode('utf-8').decode('utf-8')
            elif row[2]==target_langid:
                hl[row[1]]=row[3].encode('utf-8').decode('utf-8')
        
        print('step2')
        cur.execute("SELECT * FROM Denotations")
        while True:
            row = cur.fetchone()
            if row == None:
                break
            meaning_id=row[2]
            ex_id=row[3]
            if expr_dic[ex_id]==source_langid:
                if meaning_id in mention_dic:
                    mention_dic[meaning_id][0].append(ex_id)
                else:
                    mention_dic[meaning_id]=[[ex_id],[]]
            elif  expr_dic[ex_id]==target_langid:
                if meaning_id in mention_dic:
                    mention_dic[meaning_id][1].append(ex_id)
                else:
                    mention_dic[meaning_id]=[[],[ex_id]]

        f_out=open(os.path.join(output_directory,'%s_%s_lexicon.txt'%(source_language,target_language)),'w', encoding='utf-8')
        mm=0
        print('step3')
        for key, onepair in mention_dic.items():
            t1=[]
            t2=[]
            for one_1 in onepair[0]:
                t1.append(ll[one_1])
            for one_1 in onepair[1]:
                t2.append(hl[one_1])
                if t1!=[] and t2!=[]:
                    mm+=1
                    for ile in t1:
                        for hle in t2:
                            f_out.write('%s\t%s\n'%(ile,hle))
        f_out.close()
    print(mm)

if __name__=="__main__":
        parser = argparse.ArgumentParser(description='Extracting bi-lingual lexicion from Panlex')
        parser.add_argument('--source_language', default='', help='identify the 3-digit language code for source language')
        parser.add_argument('--target_language', default='eng', help='identify the 3-digit language code for target language')
        parser.add_argument('--output_directory', default='data/lexicons/', help='identify the path of the folder to save the extracted lexicon')
        parser.add_argument('--panlex_dir', default='data/', help='path of folder for original Panlex json files')
        parser.add_argument('--sql_database', default='data/panlex.db', help='path of processed sqlite database of panlex')
        args = parser.parse_args()
        if not os.path.exists(args.output_directory):
                os.mkdir(args.output_directory)

        # retrive the language variantion code from panlex database
        source_langid,target_langid = langid_extract(args.source_language, args.target_language, args.panlex_dir)
        if source_langid == None:
                print("Error: incorret source language code")
        if target_langid == None:
                print("Error: incorret target language code")
        else:
                assert source_langid != None and target_langid != None
                print(f"Extracting {args.source_language}_{source_langid} -- {args.target_language}_{target_langid} lexicon")

                extract_bilingual_lexicon(args.source_language, args.target_language, source_langid, target_langid, args.output_directory, args.sql_database)
        print("Extraction complated")
