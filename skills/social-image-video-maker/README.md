# Social Image Video Maker

把一个文件夹里的图片批量转成 800x960 社媒短视频，自动配随机音乐和动态贴纸。

## 适用场景

- 图片转视频
- 小红书/社媒素材批量生成
- 教育广告图、海报、封面转短视频
- 需要固定命名、按日期归档、批量自动化输出

## 默认效果

- 视频尺寸：`800x960`
- 视频时长：每张图 `7.5` 秒
- 背景：黑色画布，不做模糊背景填充
- 色调：不改变原图颜色、亮度、饱和度
- 图片：保持完整比例，居中显示
- 音乐：从 `~/Desktop/常用音乐` 随机选择
- 贴纸：从 `~/Desktop/常用贴纸` 随机选择，优先放在上方安全区域
- 输出命名：`社媒-图片转视频-YYYYMMDD-原素材<原图名>.mp4`
- 输出目录：在产出目录下自动创建 `YYYY-MM-DD` 日期文件夹

## 给同事的准备步骤

1. 安装 FFmpeg。

```bash
brew install ffmpeg
```

2. 在桌面准备素材文件夹。

```text
~/Desktop/常用音乐
~/Desktop/常用贴纸
```

音乐支持：`mp3`、`wav`、`m4a`、`aac`、`flac`

贴纸支持：`gif`、`png`、`webp`

3. 运行转换。

```bash
python3 scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output" \
  --limit 3
```

确认效果后去掉 `--limit 3`，即可批量处理全部图片。

## 常用参数

指定音乐和贴纸目录：

```bash
python3 scripts/social_image_video_maker.py \
  --input-dir "/path/to/images" \
  --output-root "/path/to/output" \
  --music-dir "/path/to/music" \
  --sticker-dir "/path/to/stickers"
```

调大贴纸：

```bash
--sticker-width 520
```

改视频时长：

```bash
--duration 8
```

固定日期：

```bash
--date 2026-06-25
```

## 验证输出

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 "/path/to/output.mp4"
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,channels,duration -of csv=p=0 "/path/to/output.mp4"
```

默认成功结果应接近：

```text
800,960,7.500000
aac,2,7.500000
```
