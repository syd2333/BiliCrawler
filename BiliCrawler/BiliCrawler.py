import requests
import json
import os
import time
import random
from datetime import datetime

def get_json_data(url, headers):
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def get_video_info(bv_number):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bv_number}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }
    data = get_json_data(url, headers)
    if data['code'] == 0:
        return data['data']
    else:
        return None

def get_related_videos(aid, max_related):
    url = f"https://api.bilibili.com/x/web-interface/view/detail?aid={aid}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
    }
    data = get_json_data(url, headers)
    if data['code'] == 0:
        related = data['data']['Related']  # 获取相关视频列表
        return [video['bvid'] for video in related][:max_related]
    else:
        return []

def get_comments(oid, num_pages):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    all_comments = []
    for page in range(1, num_pages + 1):
        url = f"https://api.bilibili.com/x/v2/reply?jsonp=jsonp&pn={page}&type=1&oid={oid}&sort=2"
        try:
            json_data = get_json_data(url, headers)
            if json_data['code'] == 0:
                replies = json_data['data']['replies']
                if not replies:
                    break
                for reply in replies:
                    comment_info = {
                        'comment': reply['content']['message'],
                        'user_name': reply['member']['uname'],
                        'user_sex': reply['member']['sex'],
                        'like_count': reply['like'],
                        'reply_count': reply['rcount'],
                        'comment_date': datetime.fromtimestamp(reply['ctime']).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    all_comments.append(comment_info)
        except (requests.exceptions.RequestException, KeyError, json.decoder.JSONDecodeError):
            print(f"获取评论数据失败,跳过视频 {oid} 的第 {page} 页评论")
    return all_comments

def save_data(start_bv, num_pages, max_related):
    video_data = get_video_info(start_bv)
    if video_data:
        print(f"开始爬取视频 {start_bv} 的数据...")
        os.makedirs(start_bv, exist_ok=True)
        video_info = {
            'title': video_data['title'],
            'pubdate': datetime.fromtimestamp(video_data['pubdate']).strftime('%Y-%m-%d %H:%M:%S'),
            'desc': video_data['desc'],  # 添加视频简介
            'stat': {
                'like': video_data['stat']['like'],
                'coin': video_data['stat']['coin'],
                'favorite': video_data['stat']['favorite'],
                'reply': video_data['stat']['reply']
            }
        }
        with open(os.path.join(start_bv, "info.txt"), 'w', encoding='utf-8') as file:
            json.dump(video_info, file, ensure_ascii=False, indent=4)
        print(f"视频 {start_bv} 的基本信息已保存")
        print(f"开始爬取视频 {start_bv} 的评论数据...")
        comments = get_comments(video_data['aid'], num_pages)
        with open(os.path.join(start_bv, "comments.txt"), 'w', encoding='utf-8') as file:
            json.dump(comments, file, ensure_ascii=False, indent=4)
        print(f"视频 {start_bv} 的评论数据已保存")
        print(f"开始爬取视频 {start_bv} 的相关视频数据...")
        related_videos = get_related_videos(video_data['aid'], max_related)
        for i, related_bv in enumerate(related_videos, start=1):
            print(f"开始爬取相关视频 {i}/{len(related_videos)}: {related_bv}")
            related_data = get_video_info(related_bv)
            if related_data:
                os.makedirs(os.path.join(start_bv, "related_videos", related_bv), exist_ok=True)
                related_info = {
                    'title': related_data['title'],
                    'pubdate': datetime.fromtimestamp(related_data['pubdate']).strftime('%Y-%m-%d %H:%M:%S'),
                    'desc': related_data['desc'], 
                    'stat': {
                        'like': related_data['stat']['like'],
                        'coin': related_data['stat']['coin'],
                        'favorite': related_data['stat']['favorite'],
                        'reply': related_data['stat']['reply']
                    }
                }
                with open(os.path.join(start_bv, "related_videos", related_bv, "info.txt"), 'w', encoding='utf-8') as file:
                    json.dump(related_info, file, ensure_ascii=False, indent=4)
                print(f"相关视频 {related_bv} 的基本信息已保存")
                print(f"开始爬取相关视频 {related_bv} 的评论数据...")
                related_comments = get_comments(related_data['aid'], num_pages)
                with open(os.path.join(start_bv, "related_videos", related_bv, "comments.txt"), 'w', encoding='utf-8') as file:
                    json.dump(related_comments, file, ensure_ascii=False, indent=4)
                print(f"相关视频 {related_bv} 的评论数据已保存")
            else:
                print(f"无法获取相关视频 {related_bv} 的数据,跳过")
        print(f"视频 {start_bv} 的相关视频数据已保存")
    else:
        print(f"无法获取视频 {start_bv} 的数据,跳过")

def main():
    start_bv = input("请输入起始视频的BV号: ")
    num_pages = int(input("请输入要爬取的评论页数: "))
    max_related = int(input("请输入视频最多的相关视频数量(1-10): "))
    max_related = max(1, min(10, max_related))
    save_data(start_bv, num_pages, max_related)
    print("爬取完成")

if __name__ == "__main__":
    main()