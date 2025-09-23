#### 使用方法：自己动手，Fork 本项目，绑定你自己的仓库账号或其他镜像服务账号

1. 在 Fork 的项目中绑定账号
    - 如果要使用自建仓库镜像服务

      在 `Settings`-`Secrets and variables`-`Actions` 选择 `New repository secret` 新建 `HUAWEI_DOCKER_USERNAME`  和 `HUAWEI_DOCKER_PASSWORD`  两个 Secrets

    - 如果需要使用其它镜像服务，例如腾讯云、阿里云等

      在 `Settings`-`Secrets and variables`-`Actions` 选择 `New repository secret` 新建 `HUAWEI_DOCKER_USERNAME`（你的其它镜像服务用户名）
      和 `HUAWEI_DOCKER_PASSWORD`（你的其它镜像服务密码）两个 Secrets

2. 在 images.txt 中填写要拉取的镜像，每行一个，不要带`docker pull`
      
4. 在 `Actions` 里选择 `拉取镜像推送` ，在右边点击 `Run workfow`

5. 在输入框中填写：
    - 仓库地址 示例：`swr.cn-east-3.myhuaweicloud.com`就是仓库域名地址
    - 空间名称/所属组织 示例：`aopkcn`其中`ghcr.io/aopkcn/installers:debian`aopkcn就是空间名称/所属组织
    - 系统架构 自行根据架构选择，如果拉取的镜像中没有将拉取失败，默认amd64

6. 最后点击 `Run workfow`等待镜像拉取推送

## 注意：自建仓库请保证GitHub能够访问，否则将无法推送！！！ 
