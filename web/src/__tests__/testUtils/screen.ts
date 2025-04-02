export const resizeWindow = (x, y) => {
  Object.assign(window, { innerWidth: x });
  Object.assign(window, { innerHeight: y });
  window.dispatchEvent(new Event("resize"));
};
