<template>
  <v-app id="inspire">
    <v-app-bar app>
      <v-progress-linear indeterminate color="yellow darken-2" v-show="loading" bottom absolute></v-progress-linear>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-toolbar-title>智能抠图</v-toolbar-title>
    </v-app-bar>

    <v-navigation-drawer
      v-model="drawer"
      fixed
      temporary
    >
    </v-navigation-drawer>

    <v-main class="grey lighten-3">
      <v-container>
        <v-row>
          <v-col>
            <v-sheet min-height="70vh" rounded="lg">
              <v-container>
                <v-row align="center">
                  <v-col align-self="center" cols="5">
                    <v-card v-show="!show_canvas">
                      <v-img :src="require('@/assets/upload.png')" contain width="100%" height="100%"  @click="begin_upload" v-show="!v_show_img"></v-img>
                      <v-img contain width="100%" height="100%" :src="previewImage" v-if="v_show_img" class="functionSubNav-image-opacity">
                      </v-img>
                      <input type="file" accept="image/jpeg" @change="uploadImage" v-show="false" id="image_input">
                    </v-card>
                    <v-card v-show="show_canvas">
                      <canvas id="editor" @mousedown="select_image"></canvas>
                      <v-card-actions><v-btn @click="submit_image" :disabled="button_disabled">提交</v-btn></v-card-actions>
                    </v-card>
                  </v-col>
                  <v-col align-self="center" cols="5" v-if="show_result">
                    <v-card>
                      <v-img :src="rest_img"></v-img>
                    </v-card>
                  </v-col>
                </v-row>
              </v-container>
            </v-sheet>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
export default {
  data: () => ({
    drawer: null,
    previewImage: require('@/assets/upload.png'),
    seg: null,
    loading: false,
    org_width: null,
    org_height: null,
    ids: new Set(),
    task_id: null,
    mask_height: null,
    mask_width: null,
    show_canvas: false,
    button_disabled: false,
    rest_img: '',
    img_file: null,
    show_result: false,
    v_show_img: false,
    config: require('@/assets/config.json')
  }),
  methods: {
    begin_upload () {
      document.getElementById('image_input').click()
    },
    uploadImage (e) {
      this.img_file = e.target.files[0]
      const reader = new FileReader()
      reader.readAsDataURL(this.img_file)
      reader.onload = this.load_image
      const form = new FormData()
      form.set('image', this.img_file)
      this.loading = true
      this.$axios.post(this.config['baseurl'] + '/detectron2_upload', form).then((response) => {
        this.seg = response.data['res']
        this.mask_height = this.seg.length
        this.mask_width = this.seg[0].length
        this.task_id = response.data['id']
        this.loading = false
        this.show_canvas = true
        this.flesh_canvas()
        console.log(response)
      }).catch((error) => {
        this.loading = false
        console.log(error)
      })
    },
    select_image (e) {
      if (this.seg != null) {
        const canvas = document.getElementById('editor')
        console.log(e)
        const x = Math.floor(e.layerX * this.mask_width / canvas.clientWidth)
        const y = Math.floor(e.layerY * this.mask_height / canvas.clientHeight)
        console.log({'x': x, 'y': y})
        console.log(canvas.width)
        if (this.seg[y] != null) {
          const id = this.seg[y][x]
          if (id != null) {
            if (!this.ids.has(id)) {
              this.ids.add(id)
            } else {
              this.ids.delete(id)
            }
            this.flesh_canvas()
          }
        }
      }
    },
    load_image (e) {
      this.v_show_img = true
      this.previewImage = e.target.result
    },
    flesh_canvas () {
      const img = new Image()
      img.src = this.previewImage
      let _this = this
      img.onload = function () {
        const canvas = document.getElementById('editor')
        _this.org_width = img.width
        _this.org_height = img.height
        canvas.width = img.width
        canvas.height = img.height
        const context = canvas.getContext('2d')
        context.drawImage(img, 0, 0, canvas.width, canvas.height)
        _this.add_mask_to_canvas(context)
      }
    },
    add_mask_to_canvas (context) {
      let _this = this
      let count = this.ids.size
      if (count > 0) {
        this.loading = true
        const canvas = document.getElementById('editor')
        canvas.classList.add('functionSubNav-image-opacity')
      }
      for (const id of this.ids) {
        const img = new Image()
        img.onload = function () {
          context.drawImage(img, 0, 0, _this.org_width, _this.org_height)
          count -= 1
          if (count === 0) {
            _this.loading = false
            const canvas = document.getElementById('editor')
            canvas.classList.remove('functionSubNav-image-opacity')
          }
        }
        img.src = this.config['baseurl'] + '/detectron2/' + this.task_id + '/' + id
      }
    },
    submit_image () {
      const data = new FormData()
      data.set('task', this.task_id)
      data.set('image', this.img_file)
      data.set('id', Array.from(this.ids))
      this.$axios.post(this.config['baseurl'] + '/lama/', data).then((res) => {
        console.log(res)
        this.rest_img = res.data['url']
        this.show_result = true
      })
    }
  },
  mounted () {
    this.$axios.get(this.config['baseurl']).then((res) => {
      console.log(res.data)
    })
  }
}
</script>

<style>
canvas {
  width: 100%;
}
.functionSubNav-image-opacity{
  -webkit-filter: blur(3px);
  filter: blur(3px);
}
</style>
