export const getApiErrorMessage = (error, fallback = 'Une erreur est survenue') => {
  const responseData = error?.response?.data;
  const detail = responseData?.detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || item?.loc?.join('.') || '')
      .filter(Boolean)
      .join(', ');
  }

  if (typeof responseData?.message === 'string') {
    return responseData.message;
  }

  return fallback;
};
