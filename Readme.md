# ifood

## 基本情况
1. 起始于： 2018年7月   
2. 相关国家和地区： 巴西


## API的获取
- 破解方法  
由于客户明确要求从web入口获取数据，并且移动端未发现有效api， 所以采用selenium+chrome（headless）+chromedriver进行
可以参考文章：[使用selenium, chrome, chromedriver 爬取使用JavaScript加载请求的页面](https://wiki.yunfutech.com/pages/viewpage.action?pageId=2293879&src=contextnavpagetreemode)
- 数据获取
每个餐馆首页,有一段js提供餐馆信息  
```
<script type="application/Id+json">
{
"@context": "http://schema.org",
    "@type": "Restaurant",
    "name": "Nutreme Fit",
    "image" : "https://d1jgln4w9al398.cloudfront.net/imagens/ce/logosgde/",
    "aggregateRating": {
        "@type": "AggregateRating",
       "ratingValue":"5.0",
        "bestRating": "5",
        "worstRating": "1",
        "reviewCount": "1"
    },
    "priceRange": "$",
    "servesCuisine": "Comida Saudável",
    "url": "https://www.ifood.com.br/delivery/",
    "address": {
        "@type": "PostalAddress",
        "addressLocality": "SANTO ANDRE",
        "addressRegion": "",
        "postalCode": "",
        "streetAddress": ", ",
        "addressCountry": "BR"
    },
    "openingHoursSpecification": [
                    {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek":"Monday",
                    "opens": "08:30",
                    "closes": "13:00"
                    }
...
	],
    "geo": {
        "@type": "GeoCoordinates",
        "latitude": "-23.665464",
        "longitude": "-46.553883"
    },
        "potentialAction":{
            "@type":"OrderAction",
            "target":{
                "@type":"EntryPoint",
                "urlTemplate":"https://www.ifood.com.br/delivery/?utm_source=MapPlaceAction",
                "inLanguage":"pt-BR",
                "actionPlatform":[
                    "http://schema.org/DesktopWebPlatform",
                    "http://schema.org/MobileWebPlatform",
                    "http://schema.org/IOSPlatform",
                    "http://schema.org/AndroidPlatform"
                ]
            },
            "deliveryMethod": "http://purl.org/goodrelations/v1#DeliveryModeOwnFleet",
            "priceSpecification": {
                "@type": "DeliveryChargeSpecification",
                "appliesToDeliveryMethod": "http://purl.org/goodrelations/v1#DeliveryModeOwnFleet",
                "priceCurrency":"BRL",
                "price": 1,
                "eligibleTransactionVolume": {
                    "@type": "PriceSpecification",
                    "priceCurrency":"BRL",
                    "price":"1"
                }
            }
        },
    "telephone": ""
}
</script>
```

## 代码地址
[gitlab](https://gitlab.yunfutech.com/uber_crawler/ifood.git)  
脚本操作见 readme.md


## 进展
2018-07-18： 提交第一版数据  
2018-08-14： 更新后的数据提交
2018-09-11: 网页返回的script数据中不再显示review_count, 所以没法判断评论数, 只能加载评论页面统计
2018-09-17: 网页增加随机跳出app广告, 添加判定和模拟点击
正常。。。


## 追加要求
2018-08-08： 不再使用之前的，州-城市-街道-号码的组合，直接按城市请求餐馆
2018-12-27:  数据保存至mongo数据库


## 使用说明

~~20180815~~  
**20180831**
1. 数据保存在 巴西0 的mongodb数据库
2. 每次启动前, 修改utils里的VERSION, 更新链接到新的表中
    ```python
    python3 update_links.py  # 将125个url更新到数据库
    ```
3. 运行主体, 巴西0数据库环境, 巴西1运行list, 其他运行info
    ```python
    chmod +x run_list.sh
    chmod +x run_info.sh
    
    ./run_list.sh  
    ./run_info.sh
    
    # 先运行list, 等一段时间后其他服务器运行info即可
    ```
    
4. 进度跟踪
    ```python
    python3 statistics.py  # 显示当前进度
    ```
4. 结果验证
    运行
    ```python
    python3 count_restaurant_by_city.py
    ```    
    会按照城市(link)为单位统计餐馆的数量, 保存在ifood/ifood_statistic的表中, 手动查看, 是否有相差较大的数据, 修改数据库并重新运行
    **如果更新了数据库环境, 需要先运行里面的init方法, 手动修改运行**
        
5. 输出结果  
    ```python
    # comments位置: ifood/data/20180804/comments
    python3 output_csv.py
    # restaurant信息输出位置: ifood/data/20180804/restaurants/all.csv
    ```
6. 数据保存
    ```
        数据保存在巴西0上的mongo数据库,运行脚本导出数据
    ```




