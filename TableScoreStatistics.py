'''
Created on Jun 12, 2021

@author: willg
'''


from matplotlib import pyplot as plt
import shutil

plt.rcParams['axes.facecolor'] = 'black'
plt.rcParams['figure.facecolor'] = 'black'
plt_x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

spine_color = (245,245,245)
axis_color = (222, 4, 4)
text_color = (222, 4, 4)
legend_color = (214, 214, 214)
import random

scores = [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15]



def adjust_color(color):
    return tuple(c/255 for c in color)

spine_color = adjust_color(spine_color)
axis_color = adjust_color(axis_color)
text_color = adjust_color(text_color)
legend_color = adjust_color(legend_color)

def main():
    
    fig = plt.figure()
    #plt.yaxis.get_major_locator().set_params(integer=True)
    ax = fig.add_subplot(111)
    plt.xticks(plt_x, labels=plt_x)
    
    

    
    for i in range(1,7):
        cur_score = 0
        cur_plt = [cur_score]
        for _ in range(12):
            cur_score += random.choice(scores) + random.choice(scores)
            cur_plt.append(cur_score)
            
        ax.plot(plt_x, cur_plt, label=f'Team {i}')
    
    
    
    
    #ax.plot(range(10))
    ax.set_xlabel('Race')
    ax.set_ylabel('Score')
    
    
    ax.spines['bottom'].set_color(spine_color)
    ax.spines['left'].set_color(spine_color)
    ax.xaxis.label.set_color(text_color)
    ax.yaxis.label.set_color(text_color)
    ax.tick_params(axis='x', colors=axis_color)
    ax.tick_params(axis='y', colors=axis_color)
    
    #Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    leg = ax.legend()
    leg.get_frame().set_edgecolor(legend_color)
    plt.setp(leg.get_texts(), color=legend_color)
    
    
    plt.show()


def lorenzi_pull():
    import requests
    from requests.structures import CaseInsensitiveDict
    
    url = "https://gb.hlorenzi.com/api/v1/graphql"
    
    headers = CaseInsensitiveDict()
    headers["Content-Type"] = "text/plain"
    
    data = 'mutation { standaloneMatchNew(token: 511562, matchData: "{\\"title\\":null,\\"date\\":null,\\"game\\":\\"\\",\\"style\\":\\"dark\\",\\"graph\\":\\"abs\\",\\"ratingMult\\":1,\\"teams\\":[{\\"tag\\":null,\\"name\\":null,\\"score\\":0,\\"penalty\\":0,\\"players\\":[{\\"name\\":\\"Hi\\",\\"flag\\":\\"\\",\\"scores\\":[0],\\"score\\":0,\\"scoreWithoutPenalty\\":0,\\"penalty\\":0},{\\"name\\":\\"Ho\\",\\"flag\\":\\"\\",\\"scores\\":[0],\\"score\\":0,\\"scoreWithoutPenalty\\":0,\\"penalty\\":0}]}],\\"ratingAdjustments\\":[]}") }'
    
    
    resp = requests.post(url, headers=headers, data=data)
    with open("yo", 'wb') as f:
        resp.raw.decode_content = True
        shutil.copyfileobj(resp.raw, f)   
    print(resp.content)
    print(resp.status_code)
    



if __name__ == '__main__':
    lorenzi_pull()
    