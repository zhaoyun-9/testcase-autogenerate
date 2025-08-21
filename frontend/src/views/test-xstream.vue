<template>
  <div class="test-bubble">
    <h1>Bubble 组件测试</h1>

    <div class="test-controls">
      <el-button @click="startTest" type="primary">开始测试</el-button>
      <el-button @click="clearTest">清空</el-button>
    </div>

    <div class="stream-container">
      <div v-for="(content, source) in streamContents" :key="source" class="stream-item">
        <Bubble
          :content="content.text"
          :typing="content.typing"
          :loading="content.status === 'loading'"
          placement="start"
          variant="outlined"
          :header="source"
          @typing-complete="onStreamFinish(source)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Bubble } from '@ant-design/x'
import { ElButton } from 'element-plus'

const streamContents = ref<Record<string, {
  text: string
  typing: boolean | { step?: number, interval?: number }
  status: 'loading' | 'success' | 'error'
}>>({})

const startTest = () => {
  // 模拟多个来源的流式输出
  const sources = ['用户', '系统', '文档解析智能体']
  const texts = [
    '这是来自用户的流式文本内容，用于测试Bubble组件的打字机效果。',
    '系统正在处理您的请求，请稍候...',
    '正在解析文档内容，提取关键信息用于生成测试用例。'
  ]

  sources.forEach((source, index) => {
    streamContents.value[source] = {
      text: texts[index],
      typing: { step: 2, interval: 50 }, // 每50ms显示2个字符
      status: 'loading'
    }
  })
}

const clearTest = () => {
  streamContents.value = {}
}

const onStreamFinish = (source: string) => {
  if (streamContents.value[source]) {
    streamContents.value[source].status = 'success'
    streamContents.value[source].typing = false
  }
  console.log(`流式输出完成: ${source}`)
}
</script>

<style scoped>
.test-bubble {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.test-controls {
  margin: 20px 0;
}

.stream-container {
  margin-top: 20px;
}

.stream-item {
  margin-bottom: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
}

.stream-item h3 {
  margin: 0 0 10px 0;
  color: #333;
}
</style>
