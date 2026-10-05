// Public portfolio home in the selected SPEC-318 editorial layout.

import { ArrowRight, ArrowUpRight } from "lucide-react";
import { Link } from "react-router-dom";
import eventflowThumbnail from "../assets/eventflow-thumbnail.svg";

import "./LandingPage.css";

const approachSteps = [
  {
    title: "Spec",
    description: "Define the problem and make the intended behavior explicit.",
  },
  {
    title: "Build",
    description: "Turn the plan into a focused, maintainable product.",
  },
  {
    title: "Validate",
    description: "Test the important flows and check the result in a browser.",
  },
  {
    title: "Release",
    description: "Deploy carefully and keep improving from evidence.",
  },
] as const;

/** Show the portfolio and project entry points without session data. */
export function LandingPage() {
  return (
    <div className="portfolio-home">
      <header className="portfolio-header">
        <div className="portfolio-container portfolio-header__inner">
          <Link className="portfolio-wordmark" to="/">
            RGAlvaro
          </Link>
          <nav className="portfolio-header__nav" aria-label="Public navigation">
            <a href="#work">Work</a>
            <Link to="/changelog">Changelog</Link>
            <Link className="portfolio-header__login" to="/login">
              Log in <ArrowUpRight aria-hidden="true" size={14} />
            </Link>
          </nav>
        </div>
      </header>

      <main className="portfolio-container">
        <section className="portfolio-hero" aria-labelledby="portfolio-title">
          <div className="portfolio-hero__intro">
            <p className="portfolio-eyebrow">Building useful things</p>
            <span className="portfolio-short-rule" aria-hidden="true" />
            <p>
              I am a software engineer building practical products for
              operational work.
            </p>
          </div>
          <div className="portfolio-hero__title">
            <span className="portfolio-index">01</span>
            <h1 id="portfolio-title">Selected work</h1>
            <p>Real problems. Thoughtful solutions.</p>
          </div>
        </section>

        <section
          className="portfolio-feature"
          id="work"
          aria-labelledby="opsdesk-title"
        >
          <div className="portfolio-feature__content">
            <div className="portfolio-section-heading">
              <span className="portfolio-index">01</span>
              <span className="portfolio-section-heading__rule" />
              <span>Featured project</span>
            </div>
            <div className="portfolio-feature__name">
              <h2 id="opsdesk-title">OpsDesk</h2>
              <span className="portfolio-status portfolio-status--available">
                <span aria-hidden="true" /> Available
              </span>
            </div>
            <p className="portfolio-feature__lead">
              An operations workspace for getting work done.
            </p>
            <p className="portfolio-feature__description">
              Organize teams, projects, tasks, and client tickets in one place.
              Built with careful permissions, tests, and a repeatable release
              process.
            </p>
            <ul className="portfolio-tech-list" aria-label="OpsDesk technology">
              <li>FastAPI</li>
              <li>React</li>
              <li>PostgreSQL</li>
              <li>Docker</li>
            </ul>
            <div className="portfolio-feature__actions">
              <Link className="portfolio-primary-link" to="/login">
                Open OpsDesk <ArrowRight aria-hidden="true" size={20} />
              </Link>
              <Link className="portfolio-text-link" to="/signup">
                Create account <ArrowUpRight aria-hidden="true" size={17} />
              </Link>
            </div>
          </div>

          <svg
            className="portfolio-feature__art"
            viewBox="0 0 560 440"
            fill="none"
            aria-hidden="true"
            focusable="false"
          >
            <circle cx="322" cy="167" r="114" fill="#4D9AEF" />
            <circle cx="484" cy="159" r="19" fill="#FF873F" />
            <circle cx="105" cy="320" r="40" fill="#1E63F1" />
            <rect
              x="180"
              y="219"
              width="337"
              height="126"
              rx="20"
              fill="#A9D5FF"
            />
            <path
              d="M170 121H314C328 121 340 133 340 147V299C340 313 352 325 366 325H399"
              stroke="#14396D"
              strokeWidth="2"
            />
            <circle cx="340" cy="242" r="8" fill="#14396D" />
            <rect x="63" y="91" width="248" height="105" rx="18" fill="white" />
            <circle cx="106" cy="140" r="20" fill="#2166F3" />
            <rect
              x="150"
              y="128"
              width="122"
              height="12"
              rx="6"
              fill="#AED5FC"
            />
            <rect
              x="150"
              y="151"
              width="83"
              height="10"
              rx="5"
              fill="#D2E7FB"
            />
            <rect
              x="330"
              y="178"
              width="129"
              height="119"
              rx="17"
              fill="#102A55"
            />
            <rect
              x="357"
              y="211"
              width="67"
              height="7"
              rx="3.5"
              fill="#5FA4F7"
            />
            <rect
              x="357"
              y="231"
              width="79"
              height="7"
              rx="3.5"
              fill="#397BD2"
            />
            <rect
              x="357"
              y="251"
              width="52"
              height="7"
              rx="3.5"
              fill="#397BD2"
            />
            <rect
              x="264"
              y="283"
              width="175"
              height="130"
              rx="18"
              fill="white"
            />
            <circle cx="351" cy="348" r="33" fill="#B2D8FF" />
            <path
              d="M338 348L348 358L365 338"
              stroke="white"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <g fill="#7DADE7">
              <circle cx="177" cy="366" r="2" />
              <circle cx="197" cy="366" r="2" />
              <circle cx="217" cy="366" r="2" />
              <circle cx="177" cy="386" r="2" />
              <circle cx="197" cy="386" r="2" />
              <circle cx="217" cy="386" r="2" />
              <circle cx="177" cy="406" r="2" />
              <circle cx="197" cy="406" r="2" />
              <circle cx="217" cy="406" r="2" />
            </g>
          </svg>
          <div className="portfolio-feature__foot" aria-hidden="true">
            <span>A practical tool for real work</span>
            <span className="portfolio-feature__foot-rule" />
            <span>Keep things moving</span>
          </div>
        </section>

        <section
          className="portfolio-approach"
          id="approach"
          aria-labelledby="approach-title"
        >
          <div className="portfolio-section-heading portfolio-section-heading--line">
            <span className="portfolio-index">02</span>
            <span className="portfolio-section-heading__rule" />
            <h2 id="approach-title">My approach</h2>
            <span className="portfolio-section-heading__fill" />
          </div>
          <ol className="portfolio-approach__steps">
            {approachSteps.map((step) => (
              <li key={step.title}>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="portfolio-next" aria-labelledby="eventflow-title">
          <div className="portfolio-next__content">
            <div className="portfolio-section-heading">
              <span className="portfolio-index">03</span>
              <span className="portfolio-section-heading__rule" />
              <span>Backend project</span>
            </div>
            <div className="portfolio-next__name">
              <h2 id="eventflow-title">EventFlow</h2>
              <span className="portfolio-status portfolio-status--team">
                <span aria-hidden="true" /> Code available
              </span>
            </div>
            <p>
              A backend for durable event ingestion and signed webhook delivery.
              PostgreSQL keeps delivery work recoverable while Celery workers
              send webhooks. Source code is public; the interface and live demo
              are still in development.
            </p>
            <a
              className="portfolio-text-link portfolio-next__source"
              href="https://github.com/RGAlvaro/eventflow"
              target="_blank"
              rel="noopener noreferrer"
            >
              View repository <ArrowUpRight aria-hidden="true" size={17} />
            </a>
          </div>
          <img
            className="portfolio-next__art"
            src={eventflowThumbnail}
            alt=""
          />
        </section>
      </main>

      <footer className="portfolio-footer">
        <div className="portfolio-container portfolio-footer__inner">
          <div className="portfolio-footer__identity">
            <span className="portfolio-wordmark">RGAlvaro</span>
            <p>Code. Systems. Progress.</p>
          </div>
          <nav aria-label="Footer navigation">
            <Link to="/changelog">Changelog</Link>
            <Link to="/terms">Terms</Link>
            <Link to="/copyright">Copyright</Link>
            <Link to="/cookies">Cookies</Link>
          </nav>
          <Link className="portfolio-footer__changelog" to="/changelog">
            Release notes <ArrowRight aria-hidden="true" size={18} />
          </Link>
        </div>
      </footer>
    </div>
  );
}
