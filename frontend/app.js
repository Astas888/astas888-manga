const app = Vue.createApp({
  data() {
    return {
      apiBase: "",
      sourceStatus: []
    };
  },
  methods: {
    async fetchSourceStatus() {
      const res = await fetch(`${this.apiBase}/api/v1/settings/source-status`);
      this.sourceStatus = await res.json();
    }
  },
  mounted() {
    this.fetchSourceStatus();
    setInterval(this.fetchSourceStatus, 5000);
  },
  template: `
    <div class="p-4 text-white bg-gray-900 min-h-screen">
      <h1 class="text-2xl font-bold mb-4">Astas888 Manga Dashboard</h1>
      <table class="table-auto w-full text-left border">
        <thead><tr><th>Source</th><th>Limit</th><th>Success</th><th>Error</th><th>Error %</th></tr></thead>
        <tbody>
          <tr v-for="s in sourceStatus" :key="s.source">
            <td>{{ s.source }}</td><td>{{ s.limit }}</td><td>{{ s.success }}</td>
            <td :class="s.error>0?'text-red-500':''">{{ s.error }}</td>
            <td>{{ s.error_rate }}%</td>
          </tr>
        </tbody>
      </table>
    </div>`
});
app.mount("#app");
