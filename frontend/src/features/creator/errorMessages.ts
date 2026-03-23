import axios from "axios";

import type { TranslationKey } from "../../shared/i18n";

type Translator = (key: TranslationKey) => string;

export function resolveRbacErrorMessage(error: unknown, t: Translator): string {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401) {
      return t("auth_error_unauthorized");
    }
    if (status === 403) {
      return t("auth_error_forbidden");
    }
  }

  return error instanceof Error ? error.message : t("error_unknown");
}
