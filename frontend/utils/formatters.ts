export const formatBytes = (bytes: number, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatSpeed = (bytes: number, ms: number) => {
  if (ms <= 0) return '∞ MB/s';
  const seconds = ms / 1000;
  const bytesPerSecond = bytes / seconds;
  return formatBytes(bytesPerSecond) + '/s';
};

export const getHex = (num: number) => {
  return '0x' + num.toString(16).padStart(4, '0').toUpperCase();
};