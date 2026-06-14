
const playlist = [
  {
    "id": 1,
    "title": "example video",
    "src": "videos/example_video.mp4"
  },
  {
    "id": 2,
    "title": "test video",
    "src": "videos/test_video.mp4"
  }
];
const player = document.getElementById('player');
const buttons = document.querySelectorAll('#playlist button');

function play(src) {
  player.src = src;
  player.play().catch(() => {});
}

buttons.forEach((button) => {
  button.addEventListener('click', () => play(button.dataset.src));
});

if (playlist.length > 0) {
  play(playlist[0].src);
}
