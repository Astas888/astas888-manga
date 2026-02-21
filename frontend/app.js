const app = Vue.createApp({
  data() {
    return {
      apiBase: "",
      sourceStatus: []
    };
  },
  methods: {
  async fetchSources() {
    const res = await fetch(`${this.apiBase}/api/v1/sources`);
    this.sources = await res.json();
  },
  async addSource() {
    if (!this.newSource) return;
    await fetch(`${this.apiBase}/api/v1/sources`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: this.newSource})
    });
    this.newSource = '';
    this.fetchSources();
  },
  async removeSource(name) {
    await fetch(`${this.apiBase}/api/v1/sources/${name}`, {method: 'DELETE'});
    this.fetchSources();
  },
  async doSearch() {
    if (this.searchQuery.length < 2) return;
    const res = await fetch(`${this.apiBase}/api/v1/search?q=${encodeURIComponent(this.searchQuery)}`);
    this.searchResults = await res.json();
  },
  // existing startDownload(), cancelJob(), etc…
},
mounted() {
  this.fetchSources();
  this.fetchStatus();
  setInterval(this.updateJobs, 5000);
}
  },
  mounted() {
    this.fetchSourceStatus();
    setInterval(this.fetchSourceStatus, 5000);
  },
  return {
  apiBase: '',
  downloadUrl: '',
  searchQuery: '',
  searchResults: [],
  sources: [],
  newSource: '',
  jobs: [],
  history: []
};
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
