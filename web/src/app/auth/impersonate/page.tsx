"use client";

import AuthFlowContainer from "@/components/auth/AuthFlowContainer";

import { useRouter } from "next/navigation";
import type { Route } from "next";
import { Formik, Form, FormikHelpers } from "formik";
import * as Yup from "yup";
import { toast } from "@opal/layouts";
import { TextFormField } from "@/components/Field";
import { Button } from "@opal/components";
import Text from "@/refresh-components/texts/Text";
import { useTranslations } from "next-intl";

export default function ImpersonatePage() {
  const router = useRouter();
  const t = useTranslations("auth.impersonate");

  const ImpersonateSchema = Yup.object().shape({
    email: Yup.string().email(t("invalidEmail")).required(t("required")),
    apiKey: Yup.string().required(t("required")),
  });

  const handleImpersonate = async (
    values: { email: string; apiKey: string },
    helpers: FormikHelpers<{ email: string; apiKey: string }>
  ) => {
    try {
      const response = await fetch("/api/tenants/impersonate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${values.apiKey}`,
        },
        body: JSON.stringify({ email: values.email }),
        credentials: "same-origin",
      });

      if (!response.ok) {
        const errorData = await response.json();
        toast.error(errorData.detail || t("failed"));
        helpers.setSubmitting(false);
      } else {
        helpers.setSubmitting(false);
        router.push("/app" as Route);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : t("failed")
      );
      helpers.setSubmitting(false);
    }
  };

  return (
    <AuthFlowContainer>
      <div className="flex flex-col w-full justify-center">
        <div className="w-full flex flex-col items-center justify-center">
          <Text as="p" headingH3 className="mb-6 text-center">
            {t("title")}
          </Text>
        </div>

        <Formik
          initialValues={{ email: "", apiKey: "" }}
          validationSchema={ImpersonateSchema}
          onSubmit={(values, helpers) => handleImpersonate(values, helpers)}
        >
          {({ isSubmitting }) => (
            <Form className="flex flex-col gap-4">
              <TextFormField
                name="email"
                type="email"
                label={t("emailLabel")}
                placeholder={t("emailPlaceholder")}
              />

              <TextFormField
                name="apiKey"
                type="password"
                label={t("apiKeyLabel")}
                placeholder={t("apiKeyPlaceholder")}
              />

              <Button disabled={isSubmitting} type="submit" width="full">
                {t("submitButton")}
              </Button>
            </Form>
          )}
        </Formik>

        <Text
          as="p"
          mainUiMuted
          text03
          className="mt-4 text-center px-4"
        >
          {t("adminNote")}
        </Text>
      </div>
    </AuthFlowContainer>
  );
}
