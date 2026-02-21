export default {
  data() {
    return {
      currentChapter: null,
      pages: [],
      pageIndex: 0
    }
  },
  mounted() {
    window.addEventListener('scroll', this.onScroll);
    window.addEventListener('keydown', this.onKey);
    this.touchStart = 0;
    window.addEventListener('touchstart', e => this.touchStart = e.touches[0].clientX);
    window.addEventListener('touchend', e => {
      const delta = e.changedTouches[0].clientX - this.touchStart;
      if (delta > 60) this.prevChapter();
      else if (delta < -60) this.nextChapter();
    });
  },
  methods: {
    onScroll() {
      if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200)
        this.loadNextPage();
    },
    onKey(e) {
      if (e.key === 'ArrowRight') this.nextChapter();
      if (e.key === 'ArrowLeft') this.prevChapter();
    },
    async loadNextPage() {
      if (this.pageIndex < this.pages.length - 1) this.pageIndex++;
    },
    nextChapter() {
      // route to next chapter
    },
    prevChapter() {
      // route to previous
    }
  }
}
