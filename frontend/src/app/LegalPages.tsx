// Static public legal pages for production-facing portfolio routes.

import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";

type LegalSection = {
  heading: string;
  body: string[];
};

type LegalPageContent = {
  eyebrow: string;
  title: string;
  updatedAt: string;
  intro: string[];
  sections: LegalSection[];
};

const sharedUpdatedAt = "2026-09-16";

const termsContent: LegalPageContent = {
  eyebrow: "Legal",
  title: "Terminos y condiciones",
  updatedAt: sharedUpdatedAt,
  intro: [
    "Estos terminos regulan el acceso y uso de OpsDesk como aplicacion portfolio y entorno demostrativo de gestion operativa.",
    "Este texto es una plantilla informativa pendiente de revision legal antes de cualquier uso comercial o contractual.",
  ],
  sections: [
    {
      heading: "Titularidad y contacto",
      body: [
        "OpsDesk se publica como proyecto portfolio bajo la marca publica RGAlvaro. Antes del despliegue definitivo deben completarse los datos legales del responsable, domicilio o medio de contacto profesional que corresponda.",
      ],
    },
    {
      heading: "Uso permitido",
      body: [
        "La aplicacion puede utilizarse para evaluar flujos de organizaciones, proyectos, tareas, tickets, notificaciones y operativa tecnica.",
        "No esta permitido intentar acceder a cuentas, proyectos, datos o recursos de terceros sin autorizacion, ni realizar pruebas abusivas contra la infraestructura.",
      ],
    },
    {
      heading: "Cuentas y datos introducidos",
      body: [
        "Las personas usuarias son responsables de la veracidad de los datos que introducen y de mantener la confidencialidad de sus credenciales.",
        "No deben introducirse secretos, datos sensibles, informacion confidencial de terceros ni informacion que no sea necesaria para evaluar la aplicacion.",
      ],
    },
    {
      heading: "Disponibilidad",
      body: [
        "OpsDesk es un proyecto portfolio y puede cambiar, interrumpirse o retirarse sin garantia de continuidad.",
        "Las funcionalidades visibles no constituyen una oferta comercial, SLA ni compromiso de soporte profesional salvo acuerdo expreso posterior.",
      ],
    },
    {
      heading: "Propiedad intelectual",
      body: [
        "El codigo, diseno, textos, marca del proyecto y documentacion asociada pertenecen a su titular salvo que se indique lo contrario.",
        "El acceso publico a la aplicacion no concede licencia para copiar, redistribuir o explotar el producto fuera de los usos permitidos.",
      ],
    },
    {
      heading: "Cambios",
      body: [
        "Estos terminos pueden actualizarse para reflejar cambios tecnicos, legales u operativos. La fecha de ultima actualizacion aparece al inicio de esta pagina.",
      ],
    },
  ],
};

const copyrightContent: LegalPageContent = {
  eyebrow: "Legal",
  title: "Copyright",
  updatedAt: sharedUpdatedAt,
  intro: [
    "Copyright (c) 2026 RGAlvaro. Todos los derechos reservados salvo indicacion expresa en contrario.",
  ],
  sections: [
    {
      heading: "Alcance",
      body: [
        "La estructura del producto, implementacion, interfaces, textos publicos, documentacion y materiales visuales propios de OpsDesk se publican como parte de un portfolio tecnico.",
        "Las tecnologias, librerias y marcas de terceros conservan sus propias licencias y titulares.",
      ],
    },
    {
      heading: "Uso del contenido",
      body: [
        "Se permite revisar la aplicacion y su repositorio con fines de evaluacion tecnica, seleccion profesional o aprendizaje personal.",
        "No se concede permiso para reutilizar la marca, vender copias del producto, extraer contenidos como producto propio o presentar el trabajo como autoria ajena.",
      ],
    },
    {
      heading: "Aviso",
      body: [
        "Si algun contenido, activo o referencia debiera atribuirse o retirarse, debe comunicarse al responsable del proyecto para su revision.",
      ],
    },
  ],
};

const cookiesContent: LegalPageContent = {
  eyebrow: "Legal",
  title: "Politica de cookies",
  updatedAt: sharedUpdatedAt,
  intro: [
    "OpsDesk utiliza actualmente cookies tecnicas necesarias para iniciar sesion y mantener una sesion autenticada segura.",
    "No se usan actualmente cookies de analitica, publicidad, marketing comportamental ni seguimiento de terceros.",
  ],
  sections: [
    {
      heading: "Cookies utilizadas",
      body: [
        "`access_token`: cookie httpOnly de corta duracion usada para autenticar peticiones de usuario.",
        "`refresh_token`: cookie httpOnly de mayor duracion usada para renovar la sesion sin volver a introducir credenciales.",
      ],
    },
    {
      heading: "Finalidad",
      body: [
        "Estas cookies son necesarias para prestar las funcionalidades solicitadas por la persona usuaria: login, rutas protegidas, APIs autenticadas y WebSockets autenticados.",
        "Al ser cookies tecnicas necesarias, no se muestra un banner de consentimiento mientras no se incorporen cookies no esenciales.",
      ],
    },
    {
      heading: "Duracion y seguridad",
      body: [
        "El token de acceso tiene una duracion corta configurada por el backend. El token de refresco tiene una duracion mayor para mantener la sesion.",
        "En produccion las cookies se configuran como httpOnly y Secure, de modo que no son accesibles desde JavaScript y solo viajan por HTTPS.",
      ],
    },
    {
      heading: "Gestion de cookies",
      body: [
        "Puedes cerrar sesion desde la aplicacion para eliminar las cookies de autenticacion emitidas por OpsDesk.",
        "Tambien puedes bloquear o eliminar cookies desde la configuracion del navegador, aunque hacerlo puede impedir el inicio de sesion o el uso normal de la aplicacion.",
      ],
    },
    {
      heading: "Cambios futuros",
      body: [
        "Si OpsDesk incorpora analitica, publicidad, medicion no exenta u otras cookies no necesarias, esta politica debera actualizarse y se implementara un mecanismo de consentimiento adecuado antes de su uso en produccion.",
      ],
    },
  ],
};

function LegalPage({ content }: { content: LegalPageContent }) {
  return (
    <main className="min-h-screen bg-surface text-ink">
      <section className="mx-auto max-w-4xl px-4 py-10 sm:py-14">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:text-brand/80"
        >
          <ArrowLeft aria-hidden="true" className="h-4 w-4" />
          OpsDesk
        </Link>
        <div className="mt-8 rounded-md border border-line bg-white p-6 shadow-panel sm:p-8">
          <p className="text-sm font-semibold uppercase tracking-wide text-brand">
            {content.eyebrow}
          </p>
          <h1 className="mt-3 text-3xl font-semibold sm:text-4xl">
            {content.title}
          </h1>
          <p className="mt-3 text-sm text-muted">
            Ultima actualizacion: {content.updatedAt}
          </p>
          <div className="mt-6 space-y-4 leading-7 text-muted">
            {content.intro.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
          <div className="mt-8 space-y-7">
            {content.sections.map((section) => (
              <section key={section.heading}>
                <h2 className="text-xl font-semibold">{section.heading}</h2>
                <div className="mt-3 space-y-3 leading-7 text-muted">
                  {section.body.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}

/** Render public terms and conditions without backend session state. */
export function TermsPage() {
  return <LegalPage content={termsContent} />;
}

/** Render public copyright information without backend session state. */
export function CopyrightPage() {
  return <LegalPage content={copyrightContent} />;
}

/** Render public cookie policy without backend session state. */
export function CookiesPage() {
  return <LegalPage content={cookiesContent} />;
}
